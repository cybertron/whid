What Have I Done?!
------------------

This is a simple application that adds some automation to the todo list
workflow I have been using for a number of years. In addition to this readme,
I have a `blog post <http://blog.nemebean.com/content/what-have-i-done>`_
that explains the origin of the tool.

.. image:: http://blog.nemebean.com/sites/blog.nemebean.com/files/styles/large/public/field/image/whid.png?itok=UolwsdD3

How it Works
============

The main window consists of three separate panes.  On the left is the input
pane.  This is where new todo items are created and managed.

On the top right is the today pane.  This displays any completed items for the
current day.

On the bottom right is the history pane.  It displays a list of the completed
items for all days contained in the history of the application.

There is also a button marked "All Days" that opens a new window containing
the completed items for all tracked days, including the current one.

When an item is marked complete (see below for details) it is added to the
current day's complete list.  Once an hour a timer fires that checks if the
date has changed, and if so it moves the current day's completed items to the
history and begins a new current day list.  In addition, all items completed
on the previous day are removed from the input box.

Note that the history is not editable.  Once a complete day has been moved to
the history it cannot be changed except by hacking the storage file.

Input Format
============

There are three main things to know about the input format:

* Each line is an item.  There is no ability to create multi-line items.

* Items are marked complete by adding three * characters to the end of the
  line.  Any item that ends with ``***`` is considered complete.  Only items
  that end with ``***`` are considered complete.  If ``***`` appears in the middle
  of a line it will not mark that item complete.

* A hierarchy is defined by - characters at the start of the line.  A line
  that starts with a - is considered the child of the previous line without
  a -.  A line with two -'s is considered the child of the previous line that
  has only a single -.  In general, a line with N -'s is considered the child
  of the last line with (N - 1) -'s.

  The levels of the hierarchy must be contiguous.  A line with two -'s preceded
  by a line with no -'s is considered a syntax error that must be fixed before
  the items can be processed.  If this situation exists, an error message will
  be displayed in the status bar.

  Be aware that if a parent item is marked complete all of the children will
  also be removed when the day rolls over.  In general a parent item should
  not be marked complete until all children are marked complete, but this is
  not enforced.

Examples
========

Basic
#####

Two items, the second is marked complete::

    write blog post
    fix bug***

Hierarchical
############

Four levels of hierarchy, with generations denoted by the item text.  Two
items are marked complete::

    parent
    -child one
    --grandchild***
    -child two
    --grandchild
    ---great grandchild***

Invalid Hierarchy
#################

A non-contiguous hierarchy.  This is an error and will prevent processing of
all items::

    parent
    --grandchild
