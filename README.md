Mailboxer
========

![Build Status](https://secure.travis-ci.org/vmalloc/mailboxer.png ) 

Mailboxer is a small server-side app that is intended for programmatic testing of mail delivery for long-running systems. It provides an SMTP server, and a simple REST api to manipulate mailboxes and queued emails.

Unlike off-the-shelf SMTP servers, in which you have to edit configuration files and/or manipulate LDAP accounts to create and delete mailboxes, Mailboxer enables you to rapidly create and dispose of mailboxes through a programmatic API. Emails arriving at nonexistent mailboxes are automatically discarded quietly, and are only collected when a mailbox exists. You then can proceed to obtain the emails that did arrive through a dedicated API.

This simplifies the "create a mailbox, trigger an action, make sure the corresponding email arrived" workflow.

The ideal purpose for this tool is testing a long-running product (such as a web service, an appliance, etc.) that sends emails to multiple destinations (e.g. alerts and status reports), and be able to write test scenarios which manipulate multiple email recipients and makes sure mail arrives properly.

Installation
============

To deploy to a server:

    $ fab deploy -H root@server -p password

To test on a vagrant machine:

    $ fab deploy_vagrant


Usage
=====

To create a new mailbox:

    $ curl -X POST http://mailboxer.mydomain.com/mailboxes -F name=myuser@somedomain.com

This will start storing incoming emails for myuser@somedomain.com. To get these emails:

    $ curl http://mailboxer.mydomain.com/messages/myuser@somedomain.com

To delete a mailbox:

    $ curl -X DELETE http://mailboxer.mydomain.com/mailboxes/myuser@somedomain.com/

To delete all mailboxes:

    $ curl -X DELETE "http://mailboxer.mydomain.com/mailboxes/*"

To get all messages in an inbox:

    $ curl http://mailboxer.mydomain.com/messages/myuser@somedomain.com

Or you can get only *unread* messages:

    $ curl http://mailboxer.mydomain.com/messages/myuser@somedomain.com/unread

Running Tests
=============

The simplest setup for test running is having two shell windows - one for running the project and the other for running the tests.

In the first window, run:

    $ fab debug

This will spawn a *tmux* session with multiple panes for each service, where the SMTP daemon will be on port 2525, and the web frontend on 8080. In the second window, run:

    $ nosetests -w tests

And you're done.