import pandas as pd
import urllib2
import hashlib

import logging
import json

from ckan import model

from ckan.plugins.core import SingletonPlugin, implements

from ckan.model import Session
from ckan.logic import NotFound, get_action

from ckanext.harvest.interfaces import IHarvester
from ckanext.harvest.model import HarvestObject

class VariantStoreHarvester(SingletonPlugin):

    implements(IHarvester)

    DEFAULT_REQUEST = {
        "variantSetIds": [],
        "referenceName": "1",
        "start": 1,
        "end": 247199719,
        "pageSize": 500000000000,
        "pageToken": None,
        "variantName": None
        }

    request_paylods = [{
         "variantSetIds": [],
         "referenceName": "1",
         "start": 1,
         "end": 247199719,
         "pageSize": 500000000000,
         "pageToken": None,
         "variantName": None
         }]

    def _fetch_data(self, host, request_payloads):
        """ Given a host and a series of request paylods, perform a variant
        search and normalize the responses into a dataframe. Serialize that
        dataframe back to a JSON object. """

        df = pd.DataFrame()

        for request_payload in request_paylods:
            request = urllib2.Request('{}/variants/search'.format(host))
            request.add_header('Content-Type', 'application/json')
            response = urllib2.urlopen(request, json.dumps(request_payload))

            data = json.loads(response.read())

            for variant in data['variants']:
                variant['names'] = ','.join(variant['names'])

                # Delete info for now.
                del variant['info']

                for call in variant['calls']:
                    call['genotype'] = ','.join([str(g) for g in call['genotype']])
                    call['genotypeLikelihood'] = ','.join([str(g) for g in call['genotypeLikelihood']])
                    # Delete 'info' for now
                    del call['info']

                variant['alternateBases'] = ','.join(variant['alternateBases'])

                calls = variant.pop('calls')

                records = [dict(variant.items() + call.items()) for call in calls]

                df = df.append(pd.DataFrame(records))

        return df.to_json(orient='records')

    @property
    def guid(self):
        """ Create a GUID based on the MD5 contents of the config """
        m = hashlib.md5()
        m.update(json.dumps(self.config))
        return m.hexdigest()

    @property
    def host(self):
        return self.config.get('host')

    @property
    def requests(self):
        return self.config.get('requests')

    @property
    def dataset_name(self):
        return self.config.get('dataset_name')

    @property
    def organization_name(self):
        return self.config.get('organization_name')

    @property
    def resource_name(self):
        return self.config.get('resource_name')

    def package(self):
        return {
            "name": self.dataset_name,
             "title": self.dataset_title,
             "owner_org": self.owner_org }

    def _set_config(self, config_str):
        """ Parse config as JSON. """
        if config_str:
            self.config = json.loads(config_str)
            log.debug('Using config: %r', self.config)
        else:
            self.config = {}

        # Take fields in DEFAULT_REQUEST and add them to config['requests']
        # if they don't exit.
        for request in self.requests:
            for k,v in DEFAULT_REQUEST.iteritems():
                if k not in request:
                    request[k] = v

    def info(self):
        return {
            'name': 'variantstore',
            'title': 'Variant Store',
            'description': 'A Variant Store instance that implements the GA4GH API'
            }

    # TODO: validate_config

    def gather_stage(self, harvest_job):
        log = logging.getLogger(__name__ + '.VariantStore.gather')
        log.debug('VariantStoreHarvester gather_stage for job: %r', harvest_job)

        obj = HarvestObject(guid = self.guid, job = harvest_job)
        obj.save()
        return [ obj.id ]

    def fetch_stage(self, harvest_object):
        self._set_config(harvest_object.job.source.config)
        data = self._fetch_data(self.host, self.requests)
        harvest_object.content = data
        harvest_object.save()
        return True

    def import_stage(self, harvest_object):
        if not harvest_object:
            log.error('No harvest object received')
            return False

        self._set_config(harvest_object.job.source.config)

        df = pd.read_json(harvest_object.content)

        tsv = df.to_tsv(sep="\t")

        context = {
            'model': model,
            'session': Session,
            'user': self._get_user_name()}

        # Query CKAN for our dataset.
        try:
            package = get_action('package_show')(context, {'id': self.dataset_name })
        except NotFound:
            package = get_action('package_create')(context, self.package)

        # Update or create the resource.
        try:
            pass
            # resource = [resource in package['resources'] if resource['name'] == self.resource_name]
        except StopIteration:
            pass
            # TODO: Create resource
