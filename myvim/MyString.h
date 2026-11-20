#ifndef _MY_STRING_H_
#define _MY_STRING_H_

#include <cstddef>     // std::size_t, std::ptrdiff_t
#include <string>      // std::string (SOURCE_STR overloads)
#include <iosfwd>      // std::ostream, std::istream forward declarations
#include <iterator>    // std::reverse_iterator, std::random_access_iterator_tag
#include <stdexcept>   // std::runtime_error (base for MyStringConversionError)
#include <type_traits> // std::enable_if, std::is_same, std::remove_const

// SOURCE_STR overloads must accept three input types: const char*,
// std::string&, and MyString&. Each public method therefore provides
// three overloads that all funnel into a single private helper.

// ---- DLL export macro (additional task 6.3) ----
// MYSTRING_BUILD_DLL is defined when building the DLL, MYSTRING_USE_DLL
// when linking against it. On non-Windows platforms the macro is empty.
#if defined(_WIN32) || defined(_WIN64)
#if defined(MYSTRING_BUILD_DLL)
#define MYSTRING_API __declspec(dllexport)
#elif defined(MYSTRING_USE_DLL)
#define MYSTRING_API __declspec(dllimport)
#else
#define MYSTRING_API
#endif
#else
#define MYSTRING_API
#endif

// Custom exception type thrown by to_int()/to_float() when the stored
// string cannot be parsed as a number (additional task 6.1).
class MYSTRING_API MyStringConversionError : public std::runtime_error
{
public:
    explicit MyStringConversionError(const std::string &what);
};

// Forward declaration of the random-access iterator template used by
// both iterator and const_iterator (additional task 6.2).
template <typename CharT>
class MyStringIterator;

class MyString
{
public:
    // Iterator type aliases: one template handles both mutable and
    // const iterators; the reverse variants come from std::reverse_iterator.
    using iterator = MyStringIterator<char>;
    using const_iterator = MyStringIterator<const char>;
    using reverse_iterator = std::reverse_iterator<iterator>;
    using const_reverse_iterator = std::reverse_iterator<const_iterator>;

    // ---- Constructors and destructor ----

    // Default constructor: creates an empty string with capacity 1.
    MyString(); // 1

    // Constructors from an existing source (C-string, std::string, MyString).
    MyString(const char *s); // 2-4
    MyString(const std::string &s);
    MyString(const MyString &str);

    // Constructors taking only the first `count` characters of the source.
    MyString(const char *s, std::size_t count); // 5-7
    MyString(const std::string &s, std::size_t count);
    MyString(const MyString &str, std::size_t count);

    // Fill constructor: `count` copies of a single character.
    MyString(std::size_t count, char ch); // 8

    // Additional task 6.1: move constructor and numeric constructors.
    MyString(MyString &&other) noexcept; // 6.1-1
    MyString(int value);                 // 6.1-2
    MyString(long value);                // 6.1-2
    MyString(long long value);           // 6.1-2
    MyString(double value);              // 6.1-3
    MyString(float value);               // 6.1-3 (delegates to double)

    // Destructor: releases the heap buffer.
    ~MyString(); // 9

    // ---- Modifiers ----

    // Sets size_ to zero but keeps the current capacity (task requirement:
    // capacity shrinks only in shrink_to_fit).
    void clear() noexcept;

    // Releases excess memory so that capacity_ == size_ + 1.
    void shrink_to_fit();

    // ---- Assignment operators ----

    // Copy-assignment from the three supported source types.
    MyString &operator=(const char *s); // 12
    MyString &operator=(const std::string &s);
    MyString &operator=(const MyString &str);

    // Assign a single character.
    MyString &operator=(char ch); // 13

    // Move-assignment (additional task 6.1).
    MyString &operator=(MyString &&str) noexcept; // 6.1-4

    // ---- Getters ----

    // Returns a pointer to a null-terminated buffer; never returns nullptr.
    const char *c_str() const noexcept; // 14
    // Number of significant characters (excluding the terminator).
    std::size_t size() const noexcept; // 15
    // Number of bytes allocated for the buffer, including the terminator.
    std::size_t capacity() const noexcept; // 16
    // True iff size_ == 0.
    bool empty() const noexcept; // 17

    // ---- insert() overloads ----

    // Insert `count` copies of `ch` at `index`.
    void insert(std::size_t index, std::size_t count, char ch); // 18
    // Insert the whole source at `index`.
    void insert(std::size_t index, const char *s); // 19-21
    void insert(std::size_t index, const std::string &s);
    void insert(std::size_t index, const MyString &str);
    // Insert the first `count` characters of the source.
    void insert(std::size_t index, const char *s, std::size_t count); // 22-24
    void insert(std::size_t index, const std::string &s, std::size_t count);
    void insert(std::size_t index, const MyString &str, std::size_t count);
    // Insert `count` characters starting at `s_index` of the source.
    void insert(std::size_t index, const char *s, std::size_t s_index, std::size_t count); // 25-27
    void insert(std::size_t index, const std::string &s, std::size_t s_index, std::size_t count);
    void insert(std::size_t index, const MyString &str, std::size_t s_index, std::size_t count);

    // Iterator-based insert (additional task 6.2). Returns iterator to the
    // first inserted character.
    iterator insert(const_iterator pos, std::size_t count, char ch);
    iterator insert(const_iterator pos, const char *str);
    iterator insert(const_iterator pos, const std::string &str);
    iterator insert(const_iterator pos, const MyString &str);

    // ---- append() overloads ----

    // Append `count` copies of `ch`.
    void append(std::size_t count, char ch); // 28
    // Append the whole source.
    void append(const char *s); // 29-31
    void append(const std::string &s);
    void append(const MyString &str);
    // Append the first `count` characters of the source.
    void append(const char *s, size_t count); // 32-34
    void append(const std::string &s, size_t count);
    void append(const MyString &str, size_t count);
    // Append `count` characters starting at `s_index` of the source.
    void append(const char *s, std::size_t s_index, size_t count); // 35-37
    void append(const std::string &s, std::size_t s_index, size_t count);
    void append(const MyString &str, std::size_t s_index, size_t count);

    // ---- erase() ----

    // Remove `count` characters starting at `index`.
    void erase(std::size_t index, std::size_t count); // 38

    // Iterator-based erase (additional task 6.2).
    iterator erase(const_iterator pos);
    iterator erase(const_iterator first, const_iterator last);

    // ---- replace() overloads ----

    // Replace `count` characters at `index` with the whole source.
    void replace(std::size_t index, std::size_t count, const char *s); // 39-41
    void replace(std::size_t index, std::size_t count, const std::string &s);
    void replace(std::size_t index, std::size_t count, const MyString &str);
    // Replace with the first `s_count` characters of the source.
    void replace(std::size_t index, std::size_t count, const char *s, std::size_t s_count); // 42-44
    void replace(std::size_t index, std::size_t count, const std::string &s, std::size_t s_count);
    void replace(std::size_t index, std::size_t count, const MyString &str, std::size_t s_count);
    // Replace with `s_count` characters starting at `s_index` of the source.
    void replace(std::size_t index, std::size_t count, const char *s, std::size_t s_index, std::size_t s_count); // 45-47
    void replace(std::size_t index, std::size_t count, const std::string &s, std::size_t s_index, std::size_t s_count);
    void replace(std::size_t index, std::size_t count, const MyString &str, std::size_t s_index, std::size_t s_count);

    // Iterator-based replace (additional task 6.2).
    MyString &replace(const_iterator first, const_iterator last, const char *str);
    MyString &replace(const_iterator first, const_iterator last, const std::string &str);
    MyString &replace(const_iterator first, const_iterator last, const MyString &str);

    // ---- substr() ----

    // Substring from `index` to the end of the string.
    MyString substr(std::size_t index) const; // 48
    // Substring of at most `count` characters starting at `index`.
    MyString substr(std::size_t index, std::size_t count) const; // 49

    // Iterator-based substr (additional task 6.2).
    MyString substr(const_iterator pos) const;
    MyString substr(const_iterator pos, std::size_t count) const;

    // ---- Concatenation operators ----

    // Returns a new MyString = *this + source (does not modify *this).
    MyString operator+(const char *s) const;        // 50
    MyString operator+(const std::string &s) const; // 51
    MyString operator+(const MyString &str) const;  // 52
    // In-place concatenation, returns *this for chaining.
    MyString &operator+=(const char *s);        // 53
    MyString &operator+=(const std::string &s); // 54
    MyString &operator+=(const MyString &str);  // 55

    // ---- Indexing ----

    // Bounds-checked access; throws std::out_of_range when index >= size().
    const char &operator[](std::size_t index) const; // 56
    char &operator[](std::size_t index);

    // ---- Comparison ----

    // Lexicographic comparison: returns -1, 0 or 1.
    int compare(const MyString &str) const; // 57
    // Boolean comparison operators, all built on top of compare().
    bool operator==(const MyString &str) const; // 58-60
    bool operator!=(const MyString &str) const;
    bool operator>=(const MyString &str) const;
    bool operator<=(const MyString &str) const;
    bool operator>(const MyString &str) const;
    bool operator<(const MyString &str) const;

    // ---- Search ----

    // Return the index of the first occurrence, or -1 when not found.
    int find(const char *s) const noexcept; // 61-63
    int find(const std::string &s) const noexcept;
    int find(const MyString &str) const noexcept;
    // Same, but start searching from the given index.
    int find(const char *s, std::size_t index) const noexcept; // 64-66
    int find(const std::string &s, std::size_t index) const noexcept;
    int find(const MyString &str, std::size_t index) const noexcept;

    // Iterator-based find of a single character (additional task 6.2).
    const_iterator find(const_iterator start, char ch) const noexcept;
    iterator find(iterator start, char ch) noexcept;

    // ---- Additional helpers (task 6.1) ----
    void push_back(char ch);                // appends one character
    void reserve(std::size_t new_capacity); // grows capacity if needed

    // Bounds-checked element access, throws std::out_of_range on failure.
    char &at(std::size_t pos);             // 6.1-8
    const char &at(std::size_t pos) const; // 6.1-8
    long long to_int() const;              // 6.1-9  (throws MyStringConversionError)
    double to_float() const;               // 6.1-10 (throws MyStringConversionError)

    // ---- Iterator access (additional task 6.2) ----
    iterator begin() noexcept;
    iterator end() noexcept;
    const_iterator begin() const noexcept;
    const_iterator end() const noexcept;
    const_iterator cbegin() const noexcept;
    const_iterator cend() const noexcept;

    reverse_iterator rbegin() noexcept;
    reverse_iterator rend() noexcept;
    const_reverse_iterator rbegin() const noexcept;
    const_reverse_iterator rend() const noexcept;
    const_reverse_iterator crbegin() const noexcept;
    const_reverse_iterator crend() const noexcept;

    // Raw pointer access, needed for the debugger exercise (task 6.3).
    char *data() noexcept { return data_; }
    const char *data() const noexcept { return data_; }

private:
    // Invariants maintained by every method:
    //   data_ != nullptr
    //   data_[size_] == '\0'
    //   capacity_ >= size_ + 1
    //   capacity_ may only decrease inside shrink_to_fit().
    char *data_;
    std::size_t size_;
    std::size_t capacity_;

    // ---- Private helpers (single source of truth for common operations) ----

    // Initialise an empty, heap-allocated, null-terminated buffer.
    void InitEmpty();
    // Initialise from a buffer of known length; the terminator is added.
    void InitFromCstr(const char *s, std::size_t len);
    // Numeric constructors (task 6.1).
    void InitFromInteger(long long value); // 6.1-2
    void InitFromDouble(double value);     // 6.1-3
    // Guarantee capacity_ >= new_size + 1, growing the buffer if needed.
    void EnsureCapacityFor(std::size_t new_size);
    // Swap contents with another instance in O(1).
    void Swap(MyString &other) noexcept;

    // Core buffer operations shared by all public overloads.
    void InsertFromBuffer(std::size_t index, const char *buf, std::size_t len);
    void AppendFromBuffer(const char *buf, std::size_t len);
    void ReplaceFromBuffer(std::size_t index, std::size_t count, const char *buf, std::size_t len);

    // Build a new MyString from [index, index + count) without touching *this.
    MyString SubstrFromIndex(std::size_t index, std::size_t count) const;
    // Build a new MyString = *this + buf without touching *this.
    MyString ConcatWithBuffer(const char *buf, std::size_t len) const;

    // Aho-Corasick (reduces to KMP for a single pattern), task 6.1-7.
    int FindAhoCorasick(const char *pattern, std::size_t pattern_len, std::size_t start) const noexcept;

    // Grant the iterator access to the private buffer/size fields.
    template <typename CharT>
    friend class MyStringIterator;
};

// ------------------------------------------------------------------------
// Random-access iterator template (additional task 6.2).
// A single template serves both mutable (CharT = char) and const
// (CharT = const char) iterators; the reverse variants come from
// std::reverse_iterator. The implementation satisfies the requirements of
// std::random_access_iterator_tag, so the iterators are compatible with
// the standard algorithms (std::sort, std::find, std::distance, ...).
// ------------------------------------------------------------------------
template <typename CharT>
class MyStringIterator
{
public:
    using iterator_category = std::random_access_iterator_tag;
    using value_type = typename std::remove_const<CharT>::type;
    using difference_type = std::ptrdiff_t;
    using pointer = CharT *;
    using reference = CharT &;

    MyStringIterator() noexcept : _ptr(nullptr) {}
    explicit MyStringIterator(pointer ptr) noexcept : _ptr(ptr) {}

    // Implicit conversion iterator -> const_iterator; the enable_if clause
    // removes this constructor when the conversion would drop constness.
    template <typename OtherCharT, typename std::enable_if<std::is_same<CharT, const OtherCharT>::value, int>::type = 0>
    MyStringIterator(const MyStringIterator<OtherCharT> &other) noexcept
        : _ptr(other._ptr) {}

    reference operator*() const noexcept { return *_ptr; }
    pointer operator->() const noexcept { return _ptr; }
    reference operator[](difference_type n) const noexcept { return _ptr[n]; }

    // Pre-increment is preferred over post-increment per the code style.
    MyStringIterator &operator++() noexcept
    {
        ++_ptr;
        return *this;
    }
    MyStringIterator operator++(int) noexcept
    {
        MyStringIterator t = *this;
        ++_ptr;
        return t;
    }
    MyStringIterator &operator--() noexcept
    {
        --_ptr;
        return *this;
    }
    MyStringIterator operator--(int) noexcept
    {
        MyStringIterator t = *this;
        --_ptr;
        return t;
    }

    MyStringIterator &operator+=(difference_type n) noexcept
    {
        _ptr += n;
        return *this;
    }
    MyStringIterator &operator-=(difference_type n) noexcept
    {
        _ptr -= n;
        return *this;
    }

    // Friend definitions allow both it + n and n + it, plus distance
    // computation between two iterators.
    friend MyStringIterator operator+(MyStringIterator it, difference_type n) noexcept
    {
        it += n;
        return it;
    }
    friend MyStringIterator operator+(difference_type n, MyStringIterator it) noexcept
    {
        it += n;
        return it;
    }
    friend MyStringIterator operator-(MyStringIterator it, difference_type n) noexcept
    {
        it -= n;
        return it;
    }
    friend difference_type operator-(const MyStringIterator &a, const MyStringIterator &b) noexcept
    {
        return a._ptr - b._ptr;
    }

    friend bool operator==(const MyStringIterator &a, const MyStringIterator &b) noexcept { return a._ptr == b._ptr; }
    friend bool operator!=(const MyStringIterator &a, const MyStringIterator &b) noexcept { return a._ptr != b._ptr; }
    friend bool operator<(const MyStringIterator &a, const MyStringIterator &b) noexcept { return a._ptr < b._ptr; }
    friend bool operator<=(const MyStringIterator &a, const MyStringIterator &b) noexcept { return a._ptr <= b._ptr; }
    friend bool operator>(const MyStringIterator &a, const MyStringIterator &b) noexcept { return a._ptr > b._ptr; }
    friend bool operator>=(const MyStringIterator &a, const MyStringIterator &b) noexcept { return a._ptr >= b._ptr; }

private:
    pointer _ptr;
    template <typename U>
    friend class MyStringIterator;
};

// Stream operators (additional task 6.1-5/6). The overloads for
// std::ofstream/std::ifstream are defined in MyString.cpp.
std::ostream &operator<<(std::ostream &os, const MyString &s);
std::istream &operator>>(std::istream &is, MyString &s);

#endif //_MY_STRING_H_