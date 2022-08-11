## Creating a new migration

In order to create a new migration, you'll need to 

* Make a new file, giving it a new 12-digit hexadecimal ID
* Add the steps in that you need manually - see previous scripts for examples
* Ensure that it properly points to the most recent revision - set the Revises correctly in the docstring and `down_revision` in the code