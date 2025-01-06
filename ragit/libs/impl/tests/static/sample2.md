# Rethinking SQLAlchemy

In this document where I will share my perspectives on SQLAlchemy and its
potential overuse in database accessing code. Drawing from my extensive
experience as a seasoned developer well-versed in various databases and
data access libraries, I have come to a realization that although
SQLAlchemy might be useful in some specific cases it may not always be the
optimal choice for every scenario. In the upcoming sections, I will delve
into my views in detail and offer insights on when SQLAlchemy might be
excessively employed, as well as when alternative approaches could be more
appropriate

# Forces the data schema to be reflected in the class attributes
This approach violates the encapsluation principle of OOP not only making
the attributes of the class visible from the outside but even worse
enforcing a one to one correspondence to the data base-schema.

Few are the times where this will be proven to be a good idea as it
eliminates the possibility to abstract the way the data are stored on the
back end from how the are been used from the client code.

In SQLAlchemy, the data schema is exposed through class attributes, and any
changes to the class attributes are automatically reflected in the database
schema. This can lead to a tight coupling between the class attributes and
the database schema, and can have some potential drawbacks:

### Lack of Information Hiding
Exposing the data schema through class attributes in SQLAlchemy can
potentially violate the principle of information hiding, which is a key
aspect of encapsulation in OOP.  Information hiding aims to hide the
internal details of an object's state and behavior from the outside world,
and allows for better abstraction and separation of concerns. However, by
reflecting the data schema in class attributes, SQLAlchemy makes the
internal state of the object (i.e., the database schema) directly
accessible from the outside, which may not be desirable in some cases.

### Tight Coupling with Database Schema
In SQLAlchemy, changes to class attributes are automatically reflected in
the database schema, enforcing a one-to-one correspondence between the
class attributes and the database schema. This can result in tight coupling
between the application code and the database schema, as any changes to the
class attributes may require corresponding changes to the database schema.
This can make it harder to evolve the data schema independently from the
application code, and can potentially lead to maintenance challenges when
dealing with complex database schema changes or multiple database backends.

### Limited Flexibility in Mapping
Reflecting the data schema in class attributes in SQLAlchemy may not
provide enough flexibility for mapping complex database schema structures
or unconventional data storage patterns to Python objects. For example, if
the database schema follows a different naming convention, or if the data
needs to be mapped to multiple tables or columns in the database, the
automatic reflection of class attributes may not be sufficient. This can
limit the flexibility and customization options in mapping between the data
schema and Python objects.

### Potential Security Concerns
Exposing the data schema through class attributes in SQLAlchemy can
potentially raise security concerns, as it may allow unauthorized access to
the underlying database schema. If the class attributes are accessible from
the outside world without proper authorization and validation checks, it
can potentially lead to security vulnerabilities, such as SQL injection
attacks or unauthorized modifications to the database schema.

### Relations between tables are complicated to write and to maintain
One of the key features of relational databases is the ability to establish
relationships between tables using foreign keys, primary keys, and other
constraints. However, defining and maintaining these relationships in
SQLAlchemy can be complicated due to the following reasons:

### Complexity of Relationship Types
Relational databases support different types of relationships, such as
one-to-many, many-to-one, and many-to-many relationships. Each type of
relationship requires a different approach to define and maintain in
SQLAlchemy. For example, one-to-many relationships involve adding foreign
key references in one table to another table, many-to-one relationships
involve using backrefs or relationship properties, and many-to-many
relationships involve using association tables. Managing these different
types of relationships and their associated complexities can be
challenging.

### Complexity of Relationship
Configurations Relationships in SQLAlchemy require configuration and
customization based on the specific use case and requirements of the
application. This includes defining relationship properties, specifying
join conditions, setting up cascading delete or update behaviors, and
handling lazy or eager loading of related objects.  Configuring and
fine-tuning these relationship properties can be complex and error-prone,
as it requires a deep understanding of SQLAlchemy's ORM features and their
interactions.

### Changes to Database Schema
As applications evolve, requirements for database schema may change. This
can involve adding or modifying relationships between tables. Maintaining
consistency and integrity of relationships in SQLAlchemy when making
changes to the database schema can be challenging, as it may involve
updating multiple parts of the application code, including model
definitions, query logic, and business logic that depends on the
relationships. Failure to properly update the relationships during schema
changes can result in data integrity issues or application errors.

### Performance Considerations
Relationships in SQLAlchemy can impact the performance of database queries
and transactions. Loading related objects eagerly or lazily, optimizing
query performance, and managing transactional boundaries can be complex and
require careful consideration of the performance implications. Incorrectly
managing relationships can lead to inefficient queries, increased database
load, and degraded application performance.

### Lack of Clear Documentation
While SQLAlchemy provides comprehensive documentation, understanding and
implementing relationships correctly can still be challenging for
developers, especially those who are new to SQLAlchemy or ORM concepts in
general. The documentation may not always cover specific use cases or
provide detailed examples for complex scenarios, which can make it
difficult to grasp the nuances of defining and maintaining relationships
correctly.

### Complexity and Learning Curve
SQLAlchemy's session management can be complex, and it may require a
significant learning curve for developers who are not familiar with its
concepts and terminology. The session introduces additional complexity
compared to simpler ORM libraries or direct SQL queries, as it involves
managing transaction boundaries, dealing with different states of objects
(i.e., transient, persistent, detached), and handling session-related
events.

### Risk of Overuse or Misuse
SQLAlchemy's session can potentially be overused or misused, leading to
performance and scalability issues. For example, keeping objects in the
session for a long time, performing excessive database queries or updates,
or not properly managing transaction boundaries can result in increased
database load, inefficient queries, or stale data in the session,
negatively impacting application performance and scalability.

### Inherent Statefulness
SQLAlchemy's session is stateful, meaning it maintains a record of objects
and their states in the session cache. This can introduce complexities when
dealing with concurrent updates or distributed systems, as the session
cache may not always reflect the current state of the database. This can
require additional coordination mechanisms or manual handling of session
cache updates to ensure consistency and correctness in multi-user or
distributed environments.

### Coupling between Session and Application Code
SQLAlchemy's session is often tightly coupled with the application code, as
it requires explicit session management and can impact how objects are
persisted, queried, or updated. This can make it harder to decouple the
application code from the ORM layer, and can potentially limit flexibility
in switching to a different ORM or data access layer in the future, if
needed.

### Potential for Code Duplication
SQLAlchemy's session can sometimes result in code duplication, as
transaction management, session handling, and object state tracking may
need to be replicated across different parts of the application code. This
can increase the risk of errors and make code maintenance more challenging,
as changes in session management logic may need to be applied in multiple
places.


### Performance
ORM introduces an additional layer of abstraction between the application
code and the database, which may result in performance overhead. ORM often
involves mapping between object-oriented models and relational databases,
which can introduce complexities such as lazy loading, eager loading, and
additional SQL queries to fetch related objects or perform joins. These
complexities can potentially impact query performance and introduce
overhead compared to writing raw SQL queries that are highly optimized for
the database.

### Flexibility and Control
ORM provides a higher-level abstraction over the database, which may limit
the flexibility and control that developers have over the database
interactions. ORM may have limitations in handling complex queries,
database-specific features, or optimizing query execution plans. Writing
raw SQL queries allows developers to have full control over the queries,
indexes, and other performance optimization techniques, which may not be
achievable or efficient with ORM.

### Learning Curve and Complexity
ORM introduces additional concepts and terminologies that developers need
to learn and understand, which may result in a steeper learning curve
compared to plain SQL. ORM may also introduce additional complexity in
handling object states, session management, or transaction boundaries,
which may require additional effort and understanding from developers.

### Coupling with Database Systems
ORM is tightly coupled with specific database systems and may have
limitations in working with different databases or handling
database-specific features. Some database systems may have unique features,
syntax, or optimizations that may not be fully supported or efficiently
utilized by ORM. Writing plain SQL queries allows developers to write
database-specific queries and leverage the unique features of different
databases.

### Maintenance and Upkeep
ORM may introduce additional maintenance overhead in managing ORM-specific
configuration, models, and mappings. Changes in the database schema or
application requirements may require updates in the ORM configuration or
models, which may need additional effort and coordination. Plain SQL
queries, on the other hand, may require less maintenance overhead as they
are typically more explicit and closely tied to the specific requirements
of the application.

# Summary
In summary, while SQLAlchemy provides powerful features for defining and
managing relationships between tables in relational databases, the
complexity of relationship types, configurations, changes to database
schema, performance considerations, and lack of clear documentation can
make it challenging to write and maintain relationships correctly in
SQLAlchemy. It requires careful planning, understanding of ORM concepts,
and attention to detail to ensure that relationships are defined and
managed accurately to ensure data integrity and application reliability.

In simple terms, while SQLAlchemy may be useful for creating relatively
simple services with UIs, like Django or Rails, it should be avoided at all
costs for backend services that require modularity, high performance, and
maintainability. This applies to other high-level ORM libraries as well, as
they try to replicate what SQL, the "800 pound gorilla" of the database
world, has been doing for decades across various platforms.

The issue is not just that SQLAlchemy and other ORM libraries attempt to
replace SQL, but also that they violate fundamental object-oriented (OO)
principles like encapsulation and interface abstractions, resulting in
inferior code compared to more traditional approaches.

As a general rule, it is advisable to steer clear of SQLAlchemy and other
ORM libraries, except for some exceptions in very simple web applications
where they may provide faster development times and other benefits


