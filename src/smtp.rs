use diesel;
use diesel::prelude::*;
use failure::Error;
use native_tls::{Identity, TlsAcceptor, TlsStream};
use schema::{email, mailbox};
use std::io::{BufRead, BufReader, Write};
use std::iter::once;
use std::net::TcpStream;
use std::ops::Deref;
use std::time::SystemTime;
use utils::{ConnectionPool, LoggedResult};

use utils::StartsWithIgnoreCase;

const _MAX_LINE_LENGTH: usize = 1024;

#[derive(Debug)]
enum SMTPVerb<'a> {
    Helo,
    Ehlo,
    MailFrom(&'a str),
    RcptTo(&'a str),
    StartTLS,
    Data,
    Quit,
}

impl<'a> SMTPVerb<'a> {
    fn is_handshake(&self) -> bool {
        match self {
            Ehlo | Helo => true,
            _ => false,
        }
    }
}

use self::SMTPVerb::*;

pub struct SMTPSession {
    data: Option<String>,
    handshake_done: bool,
    recipients: Vec<String>,
    sender: Option<String>,
    plain_stream: BufReader<TcpStream>,
    tls_stream: Option<BufReader<TlsStream<TcpStream>>>,
}

impl SMTPSession {
    pub fn new(socket: TcpStream) -> Self {
        SMTPSession {
            data: None,
            handshake_done: false,
            recipients: Vec::new(),
            sender: None,
            plain_stream: BufReader::new(socket),
            tls_stream: None,
        }
    }

    fn send_invalid_command(&mut self) -> Result<(), Error> {
        self.send_status(503, "Invalid command")
    }

    fn send_ok(&mut self) -> Result<(), Error> {
        self.send_status(250, "Ok")
    }

    fn send_status(&mut self, code: u16, msg: &str) -> Result<(), Error> {
        let string = format!("{} {}\r\n", code, msg);
        debug!("--> {:?}", string);
        self.write_all(string.as_bytes())?;
        Ok(())
    }

    fn send_extended_status(
        &mut self,
        code: u16,
        msg: &str,
        extensions: &[&str],
    ) -> Result<(), Error> {
        let mut iterator = once(msg)
            .chain(extensions.iter().map(Deref::deref))
            .peekable();

        while let Some(item) = iterator.next() {
            let string = format!(
                "{}{}{}\r\n",
                code,
                if iterator.peek().is_none() { " " } else { "-" },
                item
            );
            debug!("--> {:?}", string);

            self.write_all(string.as_bytes())?;
        }

        Ok(())
    }

    fn write_all(&mut self, data: &[u8]) -> Result<(), Error> {
        let plain_writer = &mut self.plain_stream.get_mut();
        let writer: &mut Write = if self.tls_stream.is_none() {
            plain_writer
        } else {
            self.tls_stream.as_mut().unwrap().get_mut()
        };
        writer.write_all(data).map_err(Error::from)
    }

    fn parse<'a>(&mut self, line: &'a str) -> Option<SMTPVerb<'a>> {
        if let Some(pos) = line.find(':') {
            let (command, rest) = line.split_at(pos);
            let rest = &rest[1..];
            let trimmed = command.trim();

            if trimmed.eq_ignore_ascii_case("rcpt to") {
                Some(RcptTo(parse_recipient(rest.trim()).ok()?))
            } else if trimmed.eq_ignore_ascii_case("mail from") {
                Some(MailFrom(rest.trim()))
            } else {
                error!("Unknown verb: {:?}", trimmed);
                None
            }
        } else if line.starts_with_ignore_case("ehlo ") {
            Some(Ehlo)
        } else if line.starts_with_ignore_case("helo ") {
            Some(Helo)
        } else if line.trim().eq_ignore_ascii_case("starttls") {
            Some(StartTLS)
        } else {
            let trimmed = line.trim();
            if trimmed.eq_ignore_ascii_case("data") {
                Some(Data)
            } else if trimmed.eq_ignore_ascii_case("quit") {
                Some(Quit)
            } else {
                None
            }
        }
    }

    fn read_line(&mut self) -> Result<String, Error> {
        let mut returned = String::new();
        let mut reader = self.get_reader();

        reader.read_line(&mut returned)?;
        Ok(returned)
    }

    // TODO stream should be a sum type
    fn get_reader(&mut self) -> Box<&mut dyn BufRead> {
        if self.tls_stream.is_none() {
            Box::new(&mut self.plain_stream)
        } else {
            Box::new(self.tls_stream.as_mut().unwrap())
        }
    }

    fn enqueue(&mut self, pool: &ConnectionPool) -> Result<(), Error> {
        if self.sender.is_none() {
            return Err(format_err!("Sender is missing"));
        }
        if self.data.is_none() {
            return Err(format_err!("Data is missing"));
        }

        let data = self.data.as_ref().unwrap();

        let conn = pool.get()?;

        for recipient in &self.recipients {
            if let Some(mailbox_id) = mailbox::table
                .select(mailbox::columns::id)
                .filter(mailbox::columns::address.eq(&recipient))
                .first::<i32>(&conn)
                .optional()?
            {
                diesel::insert_into(email::table)
                    .values((
                        email::columns::fromaddr.eq(self.sender.as_ref().unwrap()),
                        email::columns::mailbox_id.eq(mailbox_id),
                        email::columns::timestamp.eq(SystemTime::now()),
                        email::columns::message.eq(&data),
                        email::columns::sent_via_ssl.eq(self.tls_stream.is_some()),
                    )).execute(&conn)
                    .log_errors()?;

                diesel::update(mailbox::table.filter(mailbox::columns::id.eq(mailbox_id)))
                    .set(mailbox::columns::last_activity.eq(SystemTime::now()))
                    .execute(&conn)
                    .log_errors()?;

                debug!("Enqueued message for {}", recipient);
            } else {
                debug!("Recipient {} not found", recipient);
            }
        }
        Ok(())
    }

    fn setup_tls(&mut self) -> Result<(), Error> {
        let stream = self.plain_stream.get_mut().try_clone()?;
        let acceptor = TlsAcceptor::new(load_tls_identity())?;
        self.tls_stream = Some(BufReader::new(acceptor.accept(stream)?));
        self.handshake_done = false;
        debug!("!!! established TLS connection");
        Ok(())
    }

    pub fn run(mut self, pool: &ConnectionPool) -> Result<(), Error> {
        self.send_status(220, "Mailboxer")?;
        loop {
            let line = self.read_line()?;
            debug!("<-- {:?}", line);

            let msg = if line.is_empty() {
                Some(Quit)
            } else {
                self.parse(&line)
            };

            if msg.is_none() {
                self.send_status(500, "Syntax error")?;
                continue;
            }

            let parsed = msg.unwrap();
            debug!("Parsed: {:?}", parsed);

            if let Quit = parsed {
                let returned = self.enqueue(&pool);
                self.send_status(221, "Bye")?;
                return returned;
            }

            if self.handshake_done {
                match parsed {
                    RcptTo(recipient) => {
                        self.recipients.push(recipient.into());
                        self.send_ok()?;
                    }
                    MailFrom(sender) => {
                        if self.sender.is_some() {
                            self.send_invalid_command()?;
                        } else {
                            self.sender = Some(parse_recipient(sender)?.into());
                            self.send_ok()?;
                        }
                    }
                    StartTLS => {
                        if self.tls_stream.is_some() {
                            self.send_invalid_command()?;
                        } else {
                            self.send_status(220, "Ready to start TLS")?;
                            self.setup_tls()?;
                        }
                    }
                    Data => {
                        if self.data.is_none() {
                            self.send_status(354, "End data with <CR><LF>.<CR><LF>")?;
                            self.data = Some(read_to_end_of_data(self.get_reader())?);
                            self.send_ok()?;
                        } else {
                            self.send_invalid_command()?;
                        }
                    }
                    _ => {
                        self.send_invalid_command()?;
                    }
                }
            } else if parsed.is_handshake() {
                if let Ehlo = parsed {
                    self.send_extended_status(250, "Mailboxer", &["STARTTLS"])?;
                } else {
                    self.send_status(250, "Mailboxer")?;
                }
                self.handshake_done = true;
            } else {
                self.send_invalid_command()?;
            }
        }
    }
}

fn parse_recipient(recipient_string: &str) -> Result<&str, Error> {
    if !recipient_string.starts_with('<') || !recipient_string.ends_with('>') {
        error!("Invalid recipient string: {:?}", recipient_string);
        Err(format_err!(
            "Invalid recipient string: {}",
            recipient_string
        ))
    } else {
        Ok(&recipient_string[1..recipient_string.len() - 1])
    }
}

fn read_to_end_of_data(mut stream: Box<&mut dyn BufRead>) -> Result<String, Error> {
    let mut returned = Vec::new();
    let pattern = b"\r\n.\r\n";

    loop {
        let prev_pos = returned.len();
        let read_size = stream.read_until(b'\n', &mut returned)?;

        if read_size == 0 || returned[returned.len() - 1] != b'\n' {
            return Err(format_err!("EOF encountered"));
        }

        debug!("<-- {:?}", &returned[prev_pos..]);

        if let Some(pos) = returned
            .windows(pattern.len())
            .position(|subseq| subseq == pattern)
        {
            returned.truncate(pos);
            return String::from_utf8(returned).map_err(Error::from);
        }
    }
}

#[cfg(test)]
mod tests {

    use std::io::Cursor;

    use std::io::{BufReader, Read};

    fn check_read_to_end(data: &'static str, remainder: &'static str) {
        let buf = format!("{}\r\n.\r\n{}", data, remainder);

        assert_eq!(
            super::read_to_end_of_data(Box::new(&mut BufReader::new(buf.as_bytes()))).unwrap(),
            data
        );
    }

    #[test]
    fn test_read_to_end_of_data_no_suffix() {
        check_read_to_end("hello", "");
    }

    #[test]
    fn test_read_to_end_of_data_no_suffix_with_cr() {
        check_read_to_end("hello\rthere", "");
    }

    #[test]
    fn test_read_to_end_of_data_with_suffix_with_cr() {
        check_read_to_end("hello\rthere", "and there\r");
    }

    #[test]
    fn test_read_to_end_of_data_leaves_suffix() {
        let data = b"some data here\rwith\r\na suffix\r\n.\r\nquit\r\n";
        let mut buf_reader = Cursor::new(data.iter());
        assert!(super::read_to_end_of_data(Box::new(&mut buf_reader)).is_ok());
        let mut remainder = Vec::new();
        buf_reader.read_to_end(&mut remainder).unwrap();
        assert_eq!(String::from_utf8(remainder).unwrap(), "quit\r\n");
    }

    #[test]
    fn test_parse_recipient() {
        assert_eq!(
            super::parse_recipient("<some@email.com>".into()).unwrap(),
            "some@email.com"
        );
    }
}

fn load_tls_identity() -> Identity {
    Identity::from_pkcs12(include_bytes!("../tls_identity.pfx"), "mailboxer")
        .expect("Unable to load identity")
}
