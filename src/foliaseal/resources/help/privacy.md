# Privacy and local data

FoliaSeal is designed for local PDF signing. The application does not upload documents, selected text,
credentials, private keys, or certificate passwords automatically. Help is packaged with the
application and does not fetch remote content.

Logs are local and bounded. They may contain a path when it is needed to explain a file operation, but
they must not contain passwords, credential-store values, private keys, PDF contents, selected text,
Reason, or Location. For operational recovery, read [Troubleshooting](help:troubleshooting).
