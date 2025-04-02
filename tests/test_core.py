from sqlfingerprint import SQLFingerprinter


class TestSQLFingerprinter:
    def setup_method(self):
        self.fingerprinter = SQLFingerprinter()

    def test_simple_select(self):
        sql = "SELECT id, name FROM users WHERE age > 18"
        expected = "select id, name from users where age > ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_select_with_literals(self):
        sql = "SELECT * FROM products WHERE price > 100.50 AND category = 'electronics'"
        expected = "select * from products where price > ? and category = ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_select_with_in_clause(self):
        sql = "SELECT * FROM orders WHERE status IN ('pending', 'processing', 'shipped')"
        expected = "select * from orders where status in (?)"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_select_with_alias(self):
        sql = "SELECT u.id, u.name FROM users u WHERE u.age > 21"
        expected = "select u.id, u.name from users u where u.age > ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_select_with_join(self):
        sql = """
        SELECT o.id, c.name 
        FROM orders o 
        JOIN customers c ON o.customer_id = c.id 
        WHERE o.created_at > '2023-01-01'
        """
        expected = "select o.id, c.name from orders o join customers c on o.customer_id = c.id where o.created_at > ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_select_with_explicit_alias(self):
        sql = "SELECT u.id, u.name FROM users AS u WHERE u.created_at > '2023-01-01'"
        expected = "select u.id, u.name from users as u where u.created_at > ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_subquery(self):
        sql = """
        SELECT * FROM products 
        WHERE category_id IN (
            SELECT id FROM categories WHERE active = true
        )
        """
        expected = "select * from products where category_id in (select id from categories where active = ?)"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_subquery_with_alias(self):
        sql = """
        SELECT p.* FROM products p
        WHERE p.category_id IN (
            SELECT c.id FROM categories c WHERE c.active = true
        )
        """
        expected = "select p.* from products p where p.category_id in (select c.id from categories c where c.active = ?)"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_cte(self):
        sql = """
        WITH active_categories AS (
            SELECT id, name FROM categories WHERE active = true
        )
        SELECT p.* FROM products p
        JOIN active_categories ac ON p.category_id = ac.id
        WHERE p.price > 50
        """
        expected = "with active_categories as (select id, name from categories where active = ?) select p.* from products p join active_categories ac on p.category_id = ac.id where p.price > ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_multiple_ctes(self):
        sql = """
        WITH 
        active_categories AS (
            SELECT id, name FROM categories WHERE active = true
        ),
        premium_products AS (
            SELECT * FROM products WHERE price > 100
        )
        SELECT pp.* 
        FROM premium_products pp
        JOIN active_categories ac ON pp.category_id = ac.id
        """
        expected = "with active_categories as (select id, name from categories where active = ?), premium_products as (select * from products where price > ?) select pp.* from premium_products pp join active_categories ac on pp.category_id = ac.id"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_union(self):
        sql = """
        SELECT id, name FROM users WHERE age < 18
        UNION
        SELECT id, name FROM admins WHERE level > 3
        """
        expected = "select id, name from users where age < ? union select id, name from admins where level > ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_group_by_having(self):
        sql = """
        SELECT category, COUNT(*) as count 
        FROM products 
        GROUP BY category 
        HAVING COUNT(*) > 10
        ORDER BY count DESC
        """
        expected = "select category, count(*) as count from products group by category having count(*) > ? order by count desc"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_case_statement(self):
        sql = """
        SELECT 
            id,
            CASE 
                WHEN age < 18 THEN 'minor'
                WHEN age >= 18 AND age < 65 THEN 'adult'
                ELSE 'senior' 
            END as age_group
        FROM users
        """
        expected = "select id, case when age < ? then 'minor' when age >= ? and age < ? then 'adult' else 'senior' end as age_group from users"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_complex_joins(self):
        sql = """
        SELECT o.id, c.name, p.title
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.id
        RIGHT JOIN products p ON o.product_id = p.id
        FULL JOIN shipments s ON o.id = s.order_id
        WHERE o.created_at > '2023-01-01'
        """
        expected = "select o.id, c.name, p.title from orders o left join customers c on o.customer_id = c.id right join products p on o.product_id = p.id full join shipments s on o.id = s.order_id where o.created_at > ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_window_functions(self):
        sql = """
        SELECT 
            id, 
            department,
            salary,
            AVG(salary) OVER (PARTITION BY department) as dept_avg
        FROM employees
        WHERE hired_date > '2020-01-01'
        """
        expected = "select id, department, salary, avg(salary) over (partition by department) as dept_avg from employees where hired_date > ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_insert_statement(self):
        sql = "INSERT INTO users (name, email, age) VALUES ('John', 'john@example.com', 30)"
        expected = "insert into users (name, email, age) values (?, ?, ?)"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_update_statement(self):
        sql = "UPDATE products SET price = 99.99, updated_at = '2023-06-15' WHERE id = 123"
        expected = "update products set price = ?, updated_at = ? where id = ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_delete_statement(self):
        sql = "DELETE FROM orders WHERE created_at < '2022-01-01'"
        expected = "delete from orders where created_at < ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_recursive_cte(self):
        sql = """
        WITH RECURSIVE subordinates AS (
            SELECT employee_id, manager_id, name
            FROM employees
            WHERE employee_id = 1
            UNION ALL
            SELECT e.employee_id, e.manager_id, e.name
            FROM employees e
            INNER JOIN subordinates s ON e.manager_id = s.employee_id
        )
        SELECT * FROM subordinates
        """
        expected = "with recursive subordinates as (select employee_id, manager_id, name from employees where employee_id = ? union all select e.employee_id, e.manager_id, e.name from employees e inner join subordinates s on e.manager_id = s.employee_id) select * from subordinates"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_nested_subqueries(self):
        sql = """
        SELECT * FROM products p
        WHERE p.category_id IN (
            SELECT c.id FROM categories c 
            WHERE c.parent_id IN (
                SELECT t.id FROM top_categories t WHERE t.region = 'Europe'
            )
        )
        """
        expected = "select * from products p where p.category_id in (select c.id from categories c where c.parent_id in (select t.id from top_categories t where t.region = ?))"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_different_literal_types(self):
        sql = """
        SELECT * FROM data 
        WHERE 
            int_col = 42 AND 
            float_col = 3.14159 AND 
            text_col = 'hello' AND 
            bool_col = TRUE AND 
            date_col = '2023-06-15' AND
            null_col IS NULL
        """
        expected = "select * from data where int_col = ? and float_col = ? and text_col = ? and bool_col = ? and date_col = ? and null_col is null"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_functions_and_expressions(self):
        sql = """
        SELECT 
            COUNT(*), 
            SUM(price), 
            AVG(price), 
            CONCAT(first_name, ' ', last_name) as full_name,
            price * quantity as total
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE DATE_PART('year', created_at) = 2023
        """
        expected = "select count(*), sum(price), avg(price), concat(first_name, ' ', last_name) as full_name, price * quantity as total from orders o join users u on o.user_id = u.id where date_part(?, created_at) = ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    # def test_whitespace_normalization(self):
    #     sql1 = "SELECT id FROM users WHERE age>20"
    #     sql2 = "SELECT   id   FROM\n  users \t WHERE  age > 20"
    #     assert self.fingerprinter.fingerprint(sql1) == self.fingerprinter.fingerprint(sql2)

    def test_backticks_and_quotes(self):
        sql = "SELECT `id`, 'name' FROM `users` WHERE `age` > 20"
        expected = "select id, 'name' from users where age > ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_empty_input(self):
        sql = ""
        expected = ""
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_comments(self):
        sql = """
        -- This is a comment
        SELECT id, name /* inline comment */ FROM users
        WHERE age > 18 -- end of line comment
        """
        expected = "select id, name from users where age > ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_case_preservation(self):
        sql = "SELECT UserID, UserName FROM UserTable WHERE IsActive = TRUE"
        expected = "select userid, username from usertable where isactive = ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_uppercase_keywords(self):
        sql = "SELECT id FROM users WHERE age > 21"
        expected = "select id from users where age > ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_mixed_case_in_identifiers(self):
        sql = "SELECT userId, firstName, lastName FROM userProfile WHERE lastLogin > '2023-01-01'"
        expected = "select userid, firstname, lastname from userprofile where lastlogin > ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_mixed_case_in_aliases(self):
        sql = "SELECT uProf.userId, uProf.firstName FROM userProfile AS uProf WHERE uProf.isActive = true"
        expected = "select uprof.userid, uprof.firstname from userprofile as uprof where uprof.isactive = ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_function_case_preservation(self):
        sql = "SELECT COUNT(*), MAX(salary), MIN(startDate) FROM employees"
        expected = "select count(*), max(salary), min(startdate) from employees"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_case_preservation_in_joins(self):
        sql = "SELECT u.UserID, o.OrderID FROM Users u JOIN Orders o ON u.UserID = o.UserID"
        expected = "select u.userid, o.orderid from users u join orders o on u.userid = o.userid"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_alias_from_subquery(self):
        sql = """
        SELECT SubQ.ID, SubQ.Name 
        FROM (SELECT UserID AS ID, UserName AS Name FROM UserData WHERE RegisterDate > '2020-01-01') SubQ 
        WHERE SubQ.Name LIKE 'A%'
        """
        expected = "select subq.id, subq.name from (select userid as id, username as name from userdata where registerdate > ?) subq where subq.name like ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_lowercase_select(self):
        sql = "select id, name from users where age > 18"
        expected = "select id, name from users where age > ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_lowercase_joins(self):
        sql = "select u.id, o.order_id from users u join orders o on u.id = o.user_id where o.created_at > '2023-01-01'"
        expected = "select u.id, o.order_id from users u join orders o on u.id = o.user_id where o.created_at > ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_lowercase_subquery(self):
        sql = "select * from products where category_id in (select id from categories where active = true)"
        expected = "select * from products where category_id in (select id from categories where active = ?)"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_lowercase_complex_query(self):
        sql = """
        with active_users as (
            select id, name from users where last_login > '2023-01-01'
        )
        select au.name, count(o.id) as order_count 
        from active_users au
        left join orders o on au.id = o.user_id
        group by au.name
        having count(o.id) > 5
        order by order_count desc
        """
        expected = "with active_users as (select id, name from users where last_login > ?) select au.name, count(o.id) as order_count from active_users au left join orders o on au.id = o.user_id group by au.name having count(o.id) > ? order by order_count desc"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_mixed_case_keywords(self):
        sql = "Select id, name From users Where age > 18 Order By name Asc"
        expected = "select id, name from users where age > ? order by name asc"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_mixed_case_functions(self):
        sql = "SELECT Count(*), Avg(salary) FROM employees WHERE Substring(department, 1, 3) = 'ENG'"
        expected = "select count(*), avg(salary) from employees where substring(department, ?, ?) = ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_mixed_case_complex(self):
        sql = """
        With RecentOrders As (
            Select order_id, customer_id From Orders 
            Where created_at > '2023-01-01'
        )
        Select c.name, Count(ro.order_id) As order_count
        From Customers c
        Inner Join RecentOrders ro On c.id = ro.customer_id
        Group By c.name
        Having Count(ro.order_id) > 3
        """
        expected = "with recentorders as (select order_id, customer_id from orders where created_at > ?) select c.name, count(ro.order_id) as order_count from customers c inner join recentorders ro on c.id = ro.customer_id group by c.name having count(ro.order_id) > ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_mixed_case_insert(self):
        sql = "Insert Into Users (name, email, age) Values ('John', 'john@example.com', 30)"
        expected = "insert into users (name, email, age) values (?, ?, ?)"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_mixed_case_update(self):
        sql = "Update Products Set price = 99.99, updated_at = '2023-06-15' Where id = 123"
        expected = "update products set price = ?, updated_at = ? where id = ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_lowercase_and_uppercase_identifiers(self):
        sql = "SELECT user_id, UserName, LAST_LOGIN FROM UserAccounts WHERE status = 'active'"
        expected = "select user_id, username, last_login from useraccounts where status = ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_mixed_case_and_spacing(self):
        sql = "  Select  id,name   FROM   users  WHERE  age>=21 "
        expected = "select id, name from users where age>=?"
        assert self.fingerprinter.fingerprint(sql) == expected

    # LIKE-related test cases

    def test_simple_like(self):
        sql = "SELECT * FROM users WHERE name LIKE 'John%'"
        expected = "select * from users where name like ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_like_with_escape(self):
        sql = "SELECT * FROM products WHERE description LIKE '%15\\%%' ESCAPE '\\'"
        expected = "select * from products where description like ? escape ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_like_with_underscore(self):
        sql = "SELECT * FROM customers WHERE email LIKE '%@___.com'"
        expected = "select * from customers where email like ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_multiple_like_conditions(self):
        sql = """
        SELECT * FROM articles 
        WHERE 
            title LIKE '%database%' AND 
            tags LIKE '%sql%' AND 
            content LIKE '%performance%'
        """
        expected = "select * from articles where title like ? and tags like ? and content like ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_not_like(self):
        sql = "SELECT * FROM users WHERE name NOT LIKE 'Admin%'"
        expected = "select * from users where name not like ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_like_with_or(self):
        sql = "SELECT * FROM products WHERE name LIKE 'iPhone%' OR name LIKE 'iPad%' OR name LIKE 'Mac%'"
        expected = "select * from products where name like ? or name like ? or name like ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_like_in_subquery(self):
        sql = """
        SELECT * FROM orders 
        WHERE customer_id IN (
            SELECT id FROM customers 
            WHERE name LIKE 'A%'
        )
        """
        expected = "select * from orders where customer_id in (select id from customers where name like ?)"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_like_with_concat(self):
        sql = "SELECT * FROM users WHERE CONCAT(first_name, ' ', last_name) LIKE 'John S%'"
        expected = "select * from users where concat(first_name, ?, last_name) like ?"
        assert self.fingerprinter.fingerprint(sql) == expected

    def test_like_with_special_chars(self):
        sql = "SELECT * FROM data WHERE value LIKE '50\\_%\\_\\%' ESCAPE '\\'"
        expected = "select * from data where value like ? escape ?"
        assert self.fingerprinter.fingerprint(sql) == expected
