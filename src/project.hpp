namespace test{

/**
*  Doc for A
*/
class A{};

/**
*  Doc for B
*/
class B: public A{};

/**
*  Doc for C
*/
class C {};

/**
*  Doc for D
*
*  Some inline code: `int i`
*/
class D {};

/**
*  Doc for E
*
*  ```c++
*  int i = 0;
*  E e = {};
*  ```
*/
class E {
public:
  /**
  * brief desc
  */
  int f(){}

protected:
  /**
  * brief desc
  */
  void g(int i);

private:
  /**
  * brief desc
  */
  D h(double d = 5.0);
};

/**
*  Doc for MultiParent
*
* This references D and E
*/
class MultiParent: public B, public C, public D {};


/**
* Doc for function
*/
int my_function(int i, B b);

}