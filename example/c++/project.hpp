namespace test{

/**
*  Doc for A
*/
class A{};

/**
*  Doc for B
*
*  with some math: \f$f(x) = 6x\f$
*  other math \f[ g(y) = 12y \f] (is not picked up by xml???)
*  \f[
       |I_2|=\left| \int_{0}^T \psi(t)
             \left\{
                u(a,t)-
                \int_{\gamma(t)}^a
                \frac{d\theta}{k(\theta,t)}
                \int_{a}^\theta c(\xi)u_t(\xi,t)\,d\xi
             \right\} dt
          \right|
   \f]
*/
class B: public A{

  /**
  *  this has a function
  */
  void fn(int){}

};

/**
*  Doc for C
*/
class C {
public:
  /**
  * docs
  */
  friend class B;
  /**
  *  brief doc
  *
  *  detailed doc
  *
  *  with two paragraphs
  */
  struct inner_c{
    /**
	 * brief description
	 *
	 * Detailed desc
	 */
    double data;
  };

  /**
   * Some sort of function
   *
   * Detailed text about it
   */
  void fusrohda(bool why){
		(void)why;
  }
};

/**
*  Doc for D
*
*  Some inline code: `int i`
*/
class D {
public:

  /**
  *  brief
  *  @tparam T some template parameter
  *  @tparam N number of elements
  */
  template<typename T, int N>
  void fn(std::array<T, N> t){}

};

/**
*  Doc for E
*
*  ```c++
*  int i = 0;
*  E e = {};
*  ```
*/
struct E {
public:
  /**
  * brief desc
  */
  int f(){}


  double data = 1.0;
  std::string str{"abs"};
protected:
  /**
  * brief desc
  *
  * @param i parameter i desciption
  */
  void g(int i, double d, B b = {});

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
* Doc
*/
template<typename T> class Specialization{};


/**
* Doc with nested class
*/
template<> class Specialization<int>{
  struct Foo{};
};


/**
* brief
*/
template<typename T, typename U>
struct is_thing : std::false_type{};

/**
* brief
*/
template<typename T> struct is_thing<T, double>: std::true_type {};

/**
* brief
*/
template<typename T> struct is_thing<T, int>: std::true_type {};


/**
*  a typedef description
*/
using my_type = D;

/**
*  a templated typedef description
*/
template<typename X>
using my_template_type = is_thing<int, X>;


/**
* Doc for function
*/
int my_function(int i, B b);

/**
* why not document it?
*/
namespace nested{
}

}


struct ClassWithoutNamespace{};

/**
* function not inside of a namespace
*/
int my_function(int i, test::B b);


/**
* some macro, whatever
*/
#define TOP_LEVEL_MACRO
