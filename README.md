# Romanesco
*Romanesco* is a lightweight expenses reporting system.

We use it for tracking our spending at the item level,
later aggregating and exporting for use in further accounting.
The main use case is at point-of-purchase and as a general overview
of the current situation.

The system comes with support for parsing digital receipts from two of the biggest
grocery store chains in Sweden, ICA and Willys.

Romanesco 'learns' the categorization of articles (by referencing the latest instance in the database),
so it quickly almost automatically categorizes uploaded receipts.

In addition, there is **beta** support for automatically retrieving these receipts from Willys,
using the automation component _botccoli_.

## Installation
Cloning and running `pip install .[sqlite]` will give you a starting installation.
Romanesco is designed to be used behind some other authentication system
(communicate a unique name in the `X-Remote-User` header).
You can trivially configure your web server to enable this through e.g. basic auth.

Alternatively, you may run Romanesco locally in single-user mode.
Just execute `romanesco --single`.
This is especially suitable for development.

## Contributing
Romanesco is licensed under [the EUPL-1.2-or-later](https://joinup.ec.europa.eu/collection/eupl/eupl-guidelines-faq-infographics).
Contributions welcome!

## Attributions
The icons are derivatives of Romanesco by anooonyme from [Noun Project](https://thenounproject.com/icon/romanesco-1680562/) ([CCBY3.0](https://creativecommons.org/licenses/by/3.0/)).
