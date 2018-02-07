#! /bin/env python
"""
A tool to update s3 redirection rules on an s3 bucket
"""

import sys
import yaml
import logging
from lxml import etree


logging.basicConfig(stream=sys.stdout,
                    level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

log = logging.getLogger(__name__)


def create_routing_rule(root, prefix, replace_with):
    rr = etree.SubElement(root, "RoutingRule")

    condition = etree.SubElement(rr, "Condition")
    prefix_element = etree.Element("KeyPrefixEquals")
    prefix_element.text = prefix
    condition.append(prefix_element)

    redirect = etree.SubElement(rr, "Redirect")

    replace_element = etree.Element("ReplaceKeyPrefixWith")
    replace_element.text = replace_with
    redirect.append(replace_element)

    http_redirect_element = etree.Element("HttpRedirectCode")
    http_redirect_element.text = "307"
    redirect.append(http_redirect_element)

def main():
    with open('manifests.yml', 'r') as manifest:
        config = yaml.load(manifest)

    redirect_rules = config['redirect_rules']
    root = etree.Element("RoutingRules")

    for rule in redirect_rules:
        log.info("Adding rules for {0}".format(rule['name']))
        create_routing_rule(root, rule['prefix'], rule['replace_with'])

    log.info("Routing rules:\n" + etree.tostring(root, pretty_print=True))

if __name__ == "__main__":
    main()

