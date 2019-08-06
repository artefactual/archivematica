#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Bind PID. Command-line utility and module for requesting PID-binding against
a Handle.net server.

This module contains functionality for requesting PIDs from a Handle server
and requesting that the created PID resolve to a specified URL. It makes
Archivematica-specific assumptions and also allows for the requesting of
*qualified* PID URLs (PURLs), i.e., qualified via URL query params like
``?locatt=view:<QUALIFIER>``. It was designed against a particular API (that of
IISH) but with the goal of generalizability in mind. For this reason, a fairly
complex user configuration is required, i.e., user-supplied templates for
resolve URLs and for PID-binding HTTP request bodies. See below.

For usage run::

    ./bindpid.py -h

Example usage::

    $ ./bindpid.py 58fe1b06-ee88-41ca-9bc9-320dcac6c858 file -c bindpid.cfg
    Congratulations, you have successfully bound the handle (PID) "58fe1b06-ee88-41ca-9bc9-320dcac6c858". The following persistent URLs (PURLs) are now bound to the indicated URLs:
    http://<RESOLVER_URL>/12345/58fe1b06-ee88-41ca-9bc9-320dcac6c858?locatt=view:access => https://my-domain.org/access/12345/58fe1b06-ee88-41ca-9bc9-320dcac6c858
    http://<RESOLVER_URL>/12345/58fe1b06-ee88-41ca-9bc9-320dcac6c858?locatt=view:original => https://my-domain.org/original/12345/58fe1b06-ee88-41ca-9bc9-320dcac6c858
    http://<RESOLVER_URL>/12345/58fe1b06-ee88-41ca-9bc9-320dcac6c858?locatt=view:preservation => https://my-domain.org/preservation/12345/58fe1b06-ee88-41ca-9bc9-320dcac6c858
    http://<RESOLVER_URL>/12345/58fe1b06-ee88-41ca-9bc9-320dcac6c858 => https://my-domain.org/access/12345/58fe1b06-ee88-41ca-9bc9-320dcac6c858


PID Binding Configuration Parameters
================================================================================

- ``pid_web_service_endpoint`` - The PID webservice endpoint.

  - This is the URL to make requests to in order to create PIDs and configure
    them to resolve to specified URLs.

- ``pid_web_service_key`` - The PID webservice key.

  - This allows authentication for requests to the endpoint

- ``naming_authority`` - The naming authority.

  - This is the prefix for PIDs.


URL Templates Config Params
--------------------------------------------------------------------------------

These are user-specified string templates for URLs that PURLs (i.e., persistent
identifier URLs) should resolve to for specific types of Archivematica entity,
viz.:

- the entire DIP
- the METS file (of the DIP?)
- a specific file
- a specific file's preservation/access derivative
- a specific directory

These templates must be written using Django's templating syntax or the Jinja2
templating language. They can reference the following variables:

- naming_authority
- pid, i.e., the UUID of file or directory, or the accession number of a
  unit/transfer.

The following template variables are recognized:

- base_resolve_url_template_archive           what the DIP PURL resolves to
- base_resolve_url_template_mets              what the DIP METS PURL resolves to
- base_resolve_url_template_file              what a file/folder's PURL resolves to
- base_resolve_url_template_file_access       what a file/folder's PURL
                                                with access derivative
                                                qualifier resolves to
- base_resolve_url_template_file_preservation what a file/folder's PURL
                                                with preservation
                                                derivative qualifier
                                                resolves to
- base_resolve_url_template_file_original     what a file/folder's PURL
                                                with original derivative
                                                qualifier resolves to

Examples::

    resolve_url_template_archive:
    https://my-domain.org/dip/{{ naming_authority }}/{{ pid }}

    resolve_url_template_file:
    https://my-domain.org/access/{{ naming_authority }}/{{ pid }}

    resolve_url_template_file_preservation:
    https://my-domain.org/preservation/{{ naming_authority }}/{{ pid }}


PID Request Body Template
--------------------------------------------------------------------------------

The PID request template is another Django or Jinja2 template. This one
constructs the HTTP request body using the rendered URL templates described
above as well as other vars. The variables it has access to are:

- ``naming_authority``
- ``pid``, i.e., the desired PID
- ``base_resolve_url``, i.e., one of ``resolve_url_template_archive`` or
  ``resolve_url_template_file`` (for Package or for File/Folder, respectively)
  after they are rendered.
- ``qualified_resolve_urls``, a list of dicts (array of objects) with ``url``
  and ``qualifier`` keys (attributes) for the construction of qualified PURLs.

Example::

    <?xml version='1.0' encoding='UTF-8'?>
    <soapenv:Envelope
        xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/'
        xmlns:pid='http://my-domain.org/'>
        <soapenv:Body>
            <pid:UpsertPidRequest>
                <pid:na>{{ naming_authority }}</pid:na>
                <pid:handle>
                    <pid:pid>{{ naming_authority }}/{{ pid }}</pid:pid>
                    <pid:locAtt>
                        <pid:location weight='1' href='{{ base_resolve_url }}'/>
                        {%% for qrurl in qualified_resolve_urls %%}
                            <pid:location
                                weight='0'
                                href='{{ qrurl.url }}'
                                view='{{ qrurl.qualifier }}'/>
                        {%% endfor %%}
                    </pid:locAtt>
                </pid:handle>
            </pid:UpsertPidRequest>
        </soapenv:Body>
    </soapenv:Envelope>
"""
from __future__ import absolute_import, print_function, unicode_literals

import argparse
import os

import six.moves.configparser as configparser

try:
    from jinja2 import Template
except ImportError:
    from django.template import Context, Template
import requests


# Parameters required when requesting the binding of a handle PID.
REQ_PARAMS = (
    "naming_authority",
    "pid_web_service_endpoint",
    "pid_web_service_key",
    "handle_resolver_url",
    "pid_request_body_template",
)

# To bind a PID we require a model and a desired persistent identifier.
REQ_ENTITY_PARAMS = ("entity_type", "desired_pid")

# Parameters that may be specified in a config file instead of passed on the
# command line.
CFGABLE_PARAMS = (
    "naming_authority",
    "pid_web_service_endpoint",
    "pid_web_service_key",
    "handle_resolver_url",
    "resolve_url_template_archive",
    "resolve_url_template_mets",
    "resolve_url_template_file",
    "resolve_url_template_file_access",
    "resolve_url_template_file_preservation",
    "resolve_url_template_file_original",
    "pid_request_body_template",
    "pid_request_verify_certs",
)

CFGABLE_PARAMS_TYPES = {"pid_request_verify_certs": "boolean"}

# Maps entity type values ('file' or 'unit') to the required and optional
# resolve URL template params. This means, for example, that a PID for a file
# must be requested so that its PURL resolves to something (i.e., the value
# generated by the template refed by ``resolve_url_template_file``), but it can
# also have a *qualified* PURL (i.e., with path params ``?locatt=view:access``
# that resolves to something else (i.e., the value generated by template in
# ``resolve_url_template_file_access``).
ENTITY_TYPES = {
    "file": {
        "required": ("resolve_url_template_file",),
        "optional": (
            "resolve_url_template_file_access",
            "resolve_url_template_file_preservation",
            "resolve_url_template_file_original",
        ),
    },
    "unit": {
        "required": ("resolve_url_template_archive",),
        "optional": ("resolve_url_template_mets",),
    },
}


class BindPIDException(Exception):
    pass


def _validate(argdict):
    """Call the validation functions on the separate aspects of the handle
    server form elements.
    """
    _validate_handle_server_config(argdict)
    _validate_entity_type_required_params(argdict)


def _validate_handle_server_config(argdict):
    """Validate the argument dictionary ``argdict`` passed to ``bind_pid`` and
    ``bind_pids``.
    """
    for param in REQ_PARAMS:
        val = argdict.get(param)
        if not val:
            raise BindPIDException("A value for parameter {} is required".format(param))


def _validate_entity_type_required_params(argdict):
    """Validate entity types that we can bind PIDs to, e.g. file, unit. Ensure
    that a URL template setting has been provided for generating that PID.
    """
    for param in REQ_ENTITY_PARAMS:
        val = argdict.get(param)
        if not val:
            raise BindPIDException("A value for parameter {} is required".format(param))
    entity_type = argdict["entity_type"]
    et_validation = ENTITY_TYPES.get(entity_type)
    if not et_validation:
        raise BindPIDException(
            "The value for parameter entity_type must be one of {}".format(
                ", ".join(ENTITY_TYPES)
            )
        )
    for param in et_validation["required"]:
        if not argdict.get(param):
            raise BindPIDException(
                "To request a PID for a {}, you must also supply a value"
                " for {}".format(entity_type, param)
            )


def get_purl(pid, naming_authority, resolver_url):
    """A PURL is a function of a PID (e.g., a UUID), a naming authority (e.g.,
    '12345'), and a resolver URL."""
    if resolver_url[-1] != "/":
        resolver_url += "/"
    return "{}{}/{}".format(resolver_url, naming_authority, pid)


def get_qualified_purl(purl, qualifier):
    """Not sure if this is a handle web API or an idiosyncracy of a wrapper
    around such.
    """
    return "{}?locatt=view:{}".format(purl, qualifier)


def _render_template(template, _params):
    """Render ``template`` using ``_params`` using the Django template engine or
    Jinja2.
    """
    if "Context" in globals():  # Django templates
        context = Context(_params)
        return Template(template).render(context)
    return Template(template).render(**_params)


def _render_url_templates(argsdict):
    """Return the primary resolve URL and any qualified resolve URLs (as a
    list), based on the resolve URL templates specific to the ``'entity_type'``
    key in ``argsdict``. Also return a mapping (``purl_map``) that shows which
    PURLs should resolve to which URLs if the PID binding request should be
    successful.
    """
    purl_map = {}
    purl = get_purl(
        argsdict["desired_pid"],
        argsdict["naming_authority"],
        argsdict["handle_resolver_url"],
    )
    resolve_url_param = ENTITY_TYPES[argsdict["entity_type"]]["required"][0]
    qualified_resolve_url_params = ENTITY_TYPES[argsdict["entity_type"]]["optional"]
    qualified_resolve_urls = []
    template_params = {
        "naming_authority": argsdict["naming_authority"],
        "pid": argsdict["desired_pid"],
    }
    resolve_url = _render_template(argsdict[resolve_url_param], template_params)
    purl_map[purl] = resolve_url
    for qualified_resolve_url_param in qualified_resolve_url_params:
        # The qualifier, e.g., "preservation", is last part of the template
        # param name
        qualifier = qualified_resolve_url_param.split("_")[-1]
        qualified_purl = get_qualified_purl(purl, qualifier)
        template = argsdict.get(qualified_resolve_url_param)
        if template:
            qualified_resolve_url = _render_template(template, template_params)
            qualified_resolve_urls.append(
                {"url": qualified_resolve_url, "qualifier": qualifier}
            )
            purl_map[qualified_purl] = qualified_resolve_url
    return resolve_url, qualified_resolve_urls, purl_map


def _render_request_body(argsdict, resolve_url, qualified_resolve_urls):
    """Return a request body for the PID binding request. This is assumed to be
    an XML document specified using a Jinja2 or Django template. It may contain
    any of the following variables:
    - ``naming_authority``
    - ``pid``: the desired PID
    - ``base_resolve_url``: where the PID's PURL should resolve to
    - ``qualified_resolve_urls``: a list of dicts, each having ``url`` and
      ``qualifier`` keys.
    """
    return _render_template(
        argsdict["pid_request_body_template"],
        dict(
            naming_authority=argsdict["naming_authority"],
            pid=argsdict["desired_pid"],
            base_resolve_url=resolve_url,
            qualified_resolve_urls=qualified_resolve_urls,
        ),
    ).encode("utf8")


def bind_pid(**kwargs):
    """Requests that PID ``kwargs['desired_pid']`` be created and that it
    resolve to a specified resolve URL and possibly also one or more qualified
    resolve URLS, as given by one or more of the ``resolve_url_template_``-type
    keys in ``kwargs``. All args in kwargs dict; not gonna repeat it. Details:

    - Performs a POST request to ``pid_web_service_endpoint`` with
      ``pid_web_service_key`` in headers for authentication.
    - Request body is generated from the Jinja2/Django template given in
      ``kwargs['pid_request_body_template']
    - A 200 status code in the response is taken to indicate that the PID
      binding request was successful. No attempt is made to parse the response
      body because that is not easily generalizable.
    - Error cases observed (with IISH's handle server endpoint):

      - If the PID is malformed, a response with a 500 status code will be
        returned and the SOAP XML will contain <faultcode> and <faultstring>
        elements.
      - If the Payload is invalid XML, then the response will have a 400 status
        code and the response body will be HTML.
    """
    resolve_url, qualified_resolve_urls, purl_map = _render_url_templates(kwargs)
    request_body = _render_request_body(kwargs, resolve_url, qualified_resolve_urls)
    response = requests.post(
        kwargs["pid_web_service_endpoint"],
        data=request_body,
        headers={
            "Content-Type": "text/xml",
            "Authorization": "bearer {}".format(kwargs["pid_web_service_key"]),
        },
        verify=kwargs.get("pid_request_verify_certs", True),
    )
    if response.status_code == requests.codes.ok:
        yay_msg = (
            "Congratulations, you have successfully bound the handle"
            ' (PID) "{pid}". The following persistent URLs (PURLs) are now'
            " bound to the indicated URLs:\n{purl_map_fmted}".format(
                pid=kwargs["desired_pid"],
                purl_map_fmted="\n".join(
                    "{} => {}".format(*x) for x in purl_map.items()
                ),
            )
        )
        return yay_msg
    else:
        raise BindPIDException(
            "Request to handle server at\n{}\nwith request body\n{}\nreturned"
            " bad status code {} and response body\n{}".format(
                kwargs["pid_web_service_endpoint"],
                request_body,
                response.status_code,
                response.text,
            )
        )


def _add_parser_args(parser):
    parser.add_argument(
        "desired_pid",
        type=str,
        action="store",
        help="The PID that you want to create or whose resolve"
        " URL you want to modify.",
        default=None,
    )
    parser.add_argument(
        "entity_type",
        type=str,
        action="store",
        help="The type of entity---file or unit---that you want" " to create a PID for",
        choices=tuple(ENTITY_TYPES.keys()),
        default=None,
    )
    parser.add_argument(
        "-a",
        "--naming-authority",
        type=str,
        action="store",
        dest="naming_authority",
        help="A handle naming"
        " authority that you can create PIDs under, e.g.,"
        " 12345.",
    )
    parser.add_argument(
        "-e",
        "--pid-web-service-endpoint",
        type=str,
        action="store",
        dest="pid_web_service_endpoint",
        help="The URL to make requests to in order to create a"
        " PID and/or resolve a PID to a specific URL.",
    )
    parser.add_argument(
        "-k",
        "--pid-web-service-key",
        type=str,
        action="store",
        dest="pid_web_service_key",
        help="The web service key needed in order to make"
        " PID-creation requests to [PID_WEB_SERVICE_ENDPOINT]",
    )
    parser.add_argument(
        "-r",
        "--handle-resolver-url",
        type=str,
        action="store",
        dest="handle_resolver_url",
        help="This is the URL that generated PIDs (and"
        " qualifiers) are appended to. The resulting URL will"
        " resolve to the URL produced by the corresponding"
        " [RESOLVE_URL_TEMPLATE_] var.",
    )
    parser.add_argument(
        "-c",
        "--config-file",
        type=str,
        action="store",
        dest="config_file",
        help="Path (absolute or relative) to a config file"
        " (ini-style) that specifies values for any of the"
        " following arguments: [{}]".format(
            "], [".join(x.upper() for x in CFGABLE_PARAMS)
        ),
    )
    # Resolve URL templates: these are Django/Jinja2 templates that are used to
    # construct the URLs that PIDs/PURLs will resolve to.
    parser.add_argument(
        "--resolve-url-template-archive",
        type=str,
        action="store",
        dest="resolve_url_template_archive",
        help="Template for the URL that a DIP's PURL should" " resolve to",
        default=None,
    )
    parser.add_argument(
        "--resolve-url-template-mets",
        type=str,
        action="store",
        dest="resolve_url_template_mets",
        help="Template for"
        ' the URL that a DIP\'s PURL with the "mets" qualifier'
        " should resolve to.",
        default=None,
    )
    parser.add_argument(
        "--resolve-url-template-file",
        type=str,
        action="store",
        dest="resolve_url_template_file",
        help="Template for"
        " the URL that a file's PURL should resolve to (Note:"
        " defaults to access)",
        default=None,
    )
    parser.add_argument(
        "--resolve-url-template-file-access",
        type=str,
        action="store",
        dest="resolve_url_template_file_access",
        help="Template for the URL that a file's PURL with the"
        ' "access" qualifier should resolve to',
        default=None,
    )
    parser.add_argument(
        "--resolve-url-template-file-preservation",
        type=str,
        action="store",
        dest="resolve_url_template_file_preservation",
        help="Template for the URL that a file's PURL with the"
        ' "preservation" qualifier should resolve to',
        default=None,
    )
    parser.add_argument(
        "--resolve-url-template-file-original",
        type=str,
        action="store",
        dest="resolve_url_template_file_original",
        help="Template for the URL that a file's PURL with the"
        ' "original" qualifier should resolve to',
        default=None,
    )
    parser.add_argument(
        "--verify-certs", dest="pid_request_verify_certs", action="store_true"
    )
    parser.add_argument(
        "--no-verify-certs", dest="pid_request_verify_certs", action="store_false"
    )
    return parser, parser.parse_args()


def _parse_config(args):
    """Parse the Handle config file whose path is referenced in
    ``args.config_file``, if there is such a reference. Return a dict of config
    attributes and values or an empty dict if there is no config.
    """
    cf = args.config_file
    if not cf:
        return {}
    if not os.path.isfile(cf):
        print("Warning: there is no config file at {}".format(cf))
        return {}
    config = configparser.SafeConfigParser()
    with open(cf) as filei:
        try:
            config.read_file(filei)
        except AttributeError:
            config.readfp(filei)
    return {key: _get_config_val(config, key) for key in CFGABLE_PARAMS}


def _get_config_val(config, key):
    type_ = CFGABLE_PARAMS_TYPES.get(key, "")
    getter = getattr(config, "get" + type_)
    try:
        return getter("Handle", key)
    except configparser.NoOptionError:
        return None


def _merge_args_config(args, config):
    for arg in vars(args):
        argval = getattr(args, arg, None)
        if (argval is not None) and (config.get(arg, None) is None):
            config[arg] = argval
    return config


def get_command_line_params():
    parser = argparse.ArgumentParser(description="Request handle PIDs.")
    parser, args = _add_parser_args(parser)
    config = _parse_config(args)
    return _merge_args_config(args, config)


if __name__ == "__main__":
    params = get_command_line_params()
    try:
        msg = bind_pid(**params)
        print(msg)
    except BindPIDException as exc:
        print(exc)
