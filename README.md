
![Mailboxer Logo](https://raw.githubusercontent.com/vmalloc/mailboxer/master/webapp/public/assets/img/mailboxer-medium.png ) 

![Build Status](https://secure.travis-ci.org/vmalloc/mailboxer.png?branch=master ) 

# What is Mailboxer?

Mailboxer is a web service helping you test applications that send emails without much hassle. It lets you programmatically open virtual accounts, send emails to them, query the emails that were received and even inject faults to make the mailserver abuse senders.

# Why should I Need it?

We assume you take yourself seriously as a developer, and thus you write tests for software you create. This is awesome.

However, in some cases you need to test products that send out emails as a part of their normal operation. Some of these may be alerts, telemetry information, invites, password reset emails, and what not. This is where it usually gets ugly - do you set up a server of your own? Do you ask your local IT guy to create a mailbox for you to use?

Mailboxer fixes that.


## Create mailboxes through API, not an IT person

Creating a mailbox is just an API call away:

```
$ curlish -X POST http://your.server.address/v2/mailboxes -J address=some_user@fakedomain.com
```

From this point forward, mailboxer will start collecting emails sent to `some_user@fakedomain.com`.

## Examine e-mails through an API

```
$ curlish http://your.server.address/v2/mailboxes/some_user@fakedomain.com/emails
```

You can also query unread emails only (marking the ones returned as read):

```
$ curlish http://your.server.address/v2/mailboxes/some_user@fakedomain.com/unread_emails
```

## Supports SSL

Mailboxer supports the STARTTLS extension, and will also let you know by which method each message was sent.

## Supports fault injection (Coming soon)

Mailboxer can be instructed to abuse mail senders by closing connections unexpectedly, sleeping and lagging, and more.

## Robust

Mailboxer can sustain very high loads of email messages. The email workers are balanced by *haproxy*, and can be scaled to take more resources on more heavy duty servers.


## Vacuuming

Mailboxes automatically get cleaned up after a week of inactivity


## It's free!

Mailboxer is distributed under the BSD 3-clause license, and is completely free to use, fork or modify.


# Installation

First, clone the source files:

```
$ git clone https://github.com/vmalloc/mailboxer
$ cd mailboxer
```

Then edit the production/staging server list in your organization

```
$ cat ansible/inventories/production
[webapp]
your.server.name.here ansible_ssh_user=root

[db]
your.server.name.here ansible_ssh_user=root
```

Then just deploy:

```
$ make deploy
```
