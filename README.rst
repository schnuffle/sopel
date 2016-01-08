|version| |downloads| |license| |issues| |forks| |stars| |ages| |works| |badges|

Introduction
------------

Sopel is a simple, lightweight, open source, easy-to-use IRC Utility bot,
written in Python. It's designed to be easy to use, run and extend.

This fork deals with trying to create a flood control module.
As I do not define myself as being a software developper I tried to 
find big shoulders to stand on :-), so mostly I ripped out ideas a
concepts from various other projects, 
I'll try to mention here:

The flood detection algo is somehow ripped from cinnabot (https://github.com/glebihan/cinnabot/blob/master/Cinnabot/plugins/FloodDetection.py)
That bot uses the irc module which offers a time delayed response, that is used to trigger the unmute command
As sopel doesn't offer this, i only kept the detection algo. The unmuting is done in a seperate thread that gets it's action instruction through a threadsave dictionary.

Or least that is the idea of my design :-)

The SopelMemory handling is based on what I learned from the reading some module code, like the tell module

For the moment I still have some problems correctly declaring my dicts so that they don't change their type from SopelMemory to dict.

One additional idea popped up dealing with the code. While I'm having fun, sorting out howto deal with threads in python, the easy solution would be to use the ChanServ akick command that can do all the heavy listing for us.

The rest from this document is the normal sopel README


Installation
------------

Latest stable release
=====================
If you're on Arch, the easiest way to install is through your package
manager. The package is named ``sopel`` in [community] repository. On other
distros, and pretty much any operating system you can run Python on, you can
install `pip <https://pypi.python.org/pypi/pip/>`_, and do ``pip install
sopel``. Failing all that, you can download the latest tarball from
http://sopel.chat and follow the steps for installing from the latest
source below.

Latest source
=============
First, either clone the repository with ``git clone
git://github.com/sopel-irc/sopel.git`` or download a tarball from GitHub.

Note: sopel requires Python 2.7.x or Python 3.3+ to run. On Python 2.7,
sopel requires ``backports.ssl_match_hostname`` to be installed. Use
``pip install backports.ssl_match_hostname`` or ``yum install python-backports.ssl_match_hostname`` to install it,
or download and install it manually `from PyPi <https://pypi.python.org/pypi/backports.ssl_match_hostname>`.

In the source directory (whether cloned or from the tarball) run
``setup.py install``. You can then run ``sopel`` to configure and start the
bot. Alternately, you can just run the ``sopel.py`` file in the source
directory.

Adding modules
--------------
The easiest place to put new modules is in ``~/.sopel/modules``.

Some extra modules are available in the
`sopel-extras <https://github.com/sopel-irc/sopel-extras>`_ repository, but of
course you can also write new modules. A `tutorial <https://github.com/sopel-irc/sopel/wiki/Sopel-tutorial,-Part-2>`_
for creating new modules is available on the wiki.
API documentation can be found online at http://sopel.chat/docs, or
you can create a local version by running ``make html`` in the ``doc``
directory.

Further documentation
---------------------

In addition to the `official website <http://sopel.chat>`_, there is also a
`wiki <http://github.com/sopel-irc/sopel/wiki>`_ which includes valuable
information including a full listing of
`commands <https://github.com/sopel-irc/sopel/wiki/Commands>`_.

Questions?
----------

Join us in `#sopel <irc://irc.freenode.net/#sopel>`_ on Freenode.

.. |status| image:: https://travis-ci.org/sopel-irc/sopel.svg
   :target: https://travis-ci.org/sopel-irc/sopel
.. |coverage-status| image:: https://coveralls.io/repos/sopel-irc/sopel/badge.png
   :target: https://coveralls.io/r/sopel-irc/sopel
.. |version| image:: https://img.shields.io/pypi/v/sopel.svg
   :target: https://pypi.python.org/pypi/sopel
.. |downloads| image:: https://img.shields.io/pypi/dm/sopel.svg
   :target: https://pypi.python.org/pypi/sopel
.. |license| image:: https://img.shields.io/pypi/l/sopel.svg
   :target: https://github.com/sopel-irc/sopel/blob/master/COPYING
.. |issues| image:: https://img.shields.io/github/issues/sopel-irc/sopel.svg
   :target: https://github.com/sopel-irc/sopel/issues
.. |forks| image:: https://img.shields.io/github/forks/sopel-irc/sopel.svg
   :target: https://github.com/sopel-irc/sopel/network
.. |stars| image:: https://img.shields.io/github/stars/sopel-irc/sopel.svg
   :target: https://github.com/sopel-irc/sopel/stargazers
.. |ages| image:: https://img.shields.io/badge/ages-12%2B-green.svg
.. |works| image:: https://img.shields.io/badge/works-usually-yellow.svg
.. |badges| image:: https://img.shields.io/badge/badges-9-green.svg
