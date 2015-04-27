## The pulse of the federal .gov webspace

How the .gov domain space is doing at best practices and federal requirements.

A static website, with front-end assets managed by npm and Bower.

## Install

* Install [node and npm](https://nodejs.org/download/) directly.
* Install [bower](http://bower.io/) through npm:

```
npm install -g bower
```

* Install the [Chrome LiveReload extension](https://chrome.google.com/webstore/detail/livereload/jnihajbhpnppcggbcgedagnkighmdlei?hl=en).

## Setup

* Run the following commands to install the necessary packages:

```bash
npm install
bower install
```

* Now you should be able to run `gulp` and open the `index.html` file in your favorite browser.

```bash
gulp
```

* You'll now have your `.scss` files auto compile to `main.min.css` using a watch command. LiveReload is also a part of the process, but you'll need to make sure to have the [Chrome LiveReload extension](https://chrome.google.com/webstore/detail/livereload/jnihajbhpnppcggbcgedagnkighmdlei?hl=en) installed in whatever version of Chrome you are using.

### Public domain

This project is in the worldwide [public domain](LICENSE.md). As stated in [CONTRIBUTING](CONTRIBUTING.md):

> This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
>
> All contributions to this project will be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.
