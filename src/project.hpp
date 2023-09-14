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
*/
class D {};

/**
*  Doc for E
*/
class E {};

/**
*  Doc for MultiParent
*/
class MultiParent: public B, public C, public D, public E {};

}