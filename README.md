# Resolution Method

Determines whether a set of queries can be inferred from a given knowledge base using the resolution inference algorithm for first-order logic.

## Input

Modify these files:

* **knowledge_base.txt**: newline-delimited list of sentences
* **queries.txt**: newline-delimited list of sentences

### Format

#### Sentences

Predicate(Subject)

* **Predicate**: begins with an uppercase letter
* **Subject**
  * Constants begin with an uppercase letter
  * Variables begin with a lowercase letter

#### Operators
* **~A**: not A
* **A & B**: A and B
* **A | B**: A or B
* **A => B**: A implies B

## Output

* **output.txt**: for each query, in the order specified, a list of TRUE or FALSE will be generated if the query can be inferred from the knowledge base
