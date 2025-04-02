import re

import sqlparse
from sqlparse.sql import Token, TokenList

from .exceptions import SQLFingerprintError


class SQLFingerprinter:
    def fingerprint(self, sql):
        """Generate a normalized SQL fingerprint."""
        if not sql:
            return ""

        try:
            # Parse and format the SQL with sqlparse
            formatted = sqlparse.format(
                sql,
                keyword_case='lower',
                identifier_case='lower',
                strip_comments=True,
                reindent=True,
                normalize_whitespace=True
            )

            # Parse the formatted SQL into a statement
            parsed = sqlparse.parse(formatted)
            if not parsed:
                return ""

            stmt = parsed[0]

            # Find the SELECT clause to handle literals differently
            select_tokens = []
            in_select_clause = False

            for token in stmt.tokens:
                if token.is_keyword and token.value.lower() == 'select':
                    in_select_clause = True
                elif in_select_clause and token.is_keyword and token.value.lower() in (
                'from', 'where', 'group', 'having', 'order'):
                    in_select_clause = False

                if in_select_clause and not token.is_whitespace:
                    select_tokens.append(token)

            # Replace literals with placeholders
            def _process_token(token, in_select=False):
                # Handle string literals differently in SELECT clause
                if token.ttype in sqlparse.tokens.Literal.String and in_select:
                    return token  # Keep string literals in SELECT clause

                # Handle literals (strings, numbers)
                elif token.ttype in sqlparse.tokens.Literal:
                    return Token(token.ttype, "?")

                # Handle boolean literals
                elif token.ttype in (sqlparse.tokens.Name.Builtin, sqlparse.tokens.Keyword) and token.value.lower() in (
                        'true', 'false'):
                    return Token(token.ttype, "?")

                # Process groups recursively
                elif token.is_group:
                    for idx, child_token in enumerate(token.tokens):
                        token.tokens[idx] = _process_token(child_token, in_select)

                return token

            # Process tokens based on their location
            in_select_clause = False
            for i, token in enumerate(stmt.tokens):
                if token.is_keyword and token.value.lower() == 'select':
                    in_select_clause = True
                elif in_select_clause and token.is_keyword and token.value.lower() in (
                'from', 'where', 'group', 'having', 'order'):
                    in_select_clause = False

                stmt.tokens[i] = _process_token(token, in_select_clause)

            # Convert back to string
            sql = str(stmt)

            # Normalize IN clauses with multiple values
            sql = re.sub(r'in\s*\(\s*\?(?:\s*,\s*\?)+\s*\)', 'in (?)', sql, flags=re.IGNORECASE)

            # Ensure consistent spacing around parentheses for subqueries
            sql = re.sub(r'\(\s+', '( ', sql)
            sql = re.sub(r'\s+\)', ' )', sql)

            # Make sure all keywords are lowercase (especially for LIKE which seems to be missed)
            for keyword in ['like', 'in', 'and', 'or', 'not', 'exists', 'is null']:
                sql = re.sub(rf'\b{keyword}\b', keyword, sql, flags=re.IGNORECASE)

            # Final whitespace cleanup
            sql = re.sub(r'\s+', ' ', sql)

            # Remove backticks around identifiers
            sql = re.sub(r'`([^`]+)`', r'\1', sql)

            return sql.strip()

        except Exception as e:
            raise SQLFingerprintError(f"Fingerprint failed: {str(e)}") from e
