namespace test{

/**
*  Doc for A
*/
class A{};

/**
*  Doc for B
*
*  with some math: \f$f(x) = 6x\f$
*  other math \f(g(y) = 12y\f) (is not picked up by xml???)
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
class B: public A{};

/**
*  Doc for C
*/
class C {
public:
  /**
  *  brief doc
  *
  *  detailed doc
  */
  struct inner_c{
    double data;
  };
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
class E {
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
* brief
*/
template<typename T, typename U>
struct is_thing : std::false_type{};

/**
* brief
*/
template<typename T> struct is_thing<T, double>: std::true_type {};


/**
* Doc for function
*/
int my_function(int i, B b);

}