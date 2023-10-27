# Myst Doc

This used myst *hopefully*

Function is {cpp:func}`this <void X::A::Print_Message()>`


```{cpp:class} MyClass : public MyBase, public MyOtherBase

Some documentation for MyClass
```


```{cpp:class} test::ClassAA

Documentation of {any}`ClassAA`
```


```{cpp:class} test::ClassBB: public test::ClassAA

Documentation of ClassBB
```


```{cpp:class} ClassCC

Documentation
```


```{cpp:class} ClassDD

Documentation
```


````{cpp:class} MultiParents2: public test::ClassBB, public ClassCC, public ClassDD

Documentation with a url: <https://www.sphinx-doc.org/en/master/tutorial/describing-code.html>


```{cpp:class} MultiParents2::NestedClass2

Doc for nested class
```
````

```{cpp:class} MultiParentsNewLine: \
               public ClassB, \
               public ClassC, \
               public ClassD

Doesn't work :(
```
