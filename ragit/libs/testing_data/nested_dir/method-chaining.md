# Pure Stylistic Comment about method chaining

In what is called "modern" programming style, it is very frequent to return
"self" from a function implying possible method chaining on the client side.

An example of this style can be seen here:

```python
class Image:
    """Simple image representation
    Usage Example:
    image = Image("road.jpg")
    image.circle(image.width / 2, image.height / 2, 50). \
       text("hello", 0, 0, "GREEN", 5).rectangle(0, 0, 50, 60, "WHITE"). \
       write("output.jpg")
    """
```

## My personal style / preference


I know that chaining is used in several python libs (first one that comes to my
mind is pandas) and even more in javascript and C#  but still I am not sold on
this style (except some very special cases)..


In my case I try to refrain from using this idiom (with a few exceptions as
always of course). A typical exception can be certainly seen in JavaScript
where chaining has become a fundamental way to use libraries like jQuery or
React for example.


As the rule of thump though I do not find the resulted code to be easy
enough to read and also debuging is becoming a bit more difficult.  Also
since the produced code usually spans in several lines which makes it
harder to understand since you need to keep an eye to the opening
statemen..

Good comment from [Guido](https://mail.python.org/pipermail/python-dev/2003-October/038855.html) on this topic..

\pagebreak

## A typical case of method chaining from C++

The most common use case that I admit I have used thousands of times in my
life can be seen in this snip:

```C++
cout << "hello" << " " << "world." << endl;
```

This is using operator overloading in conjuction to method chaining to use
the resulting syntactic sugar (!) to provide a "scalable" stream writer (or
reader when using cin).

Considering the above example as very representative and also extemely
well thought application of chaining leaves me not completely satisfied as
a user.

Guess what?


In my case whenever I have to write the stdout in C++ almost always I
will simply use printf (C) instead of its C++ alternative (cout).



The reason it that the use contracts are becoming complicated to the point
that I almost never can get them right by memory at the first call. see
this for example:

C
```
printf("0x%04x\n", 0x424);
```

C++
```
std::cout << "0x" << std::hex << std::setfill('0') << std::setw(4) << 0x424 << std::endl;
```

I took this example from [here](https://stackoverflow.com/questions/2872543/printf-vs-cout-in-c)





