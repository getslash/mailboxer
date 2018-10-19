CREATE TABLE email (
id SERIAL PRIMARY KEY,
mailbox_id INTEGER NOT NULL,
fromaddr VARCHAR NOT NULL,
message TEXT NOT NULL,
"timestamp" TIMESTAMP NOT NULL,
sent_via_ssl BOOLEAN NOT NULL,
read BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE mailbox (
id SERIAL PRIMARY KEY,
address VARCHAR NOT NULL,
last_activity TIMESTAMP NOT NULL DEFAULT now()
);


CREATE INDEX ix_email_mailbox_id ON email USING btree (mailbox_id);
CREATE INDEX ix_email_timestamp ON email USING btree ("timestamp");
CREATE UNIQUE INDEX ix_mailbox_address ON mailbox USING btree (address);

CREATE INDEX ix_mailbox_last_activity ON mailbox USING btree (last_activity);
CREATE INDEX ix_mailbox_read_timestamp ON email USING btree (mailbox_id, read, "timestamp");


ALTER TABLE ONLY email
ADD CONSTRAINT email_mailbox_id_fkey FOREIGN KEY (mailbox_id) REFERENCES mailbox(id) ON DELETE CASCADE;
