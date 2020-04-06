import angular from 'angular';
import Base64 from 'base64-helpers';
// TODO rework the API in a way that's easier to use with Restangular?
// The original API requires its body formatted in a way that
// Restangular is not very good at.

// Supports creating transfers by:
// a) Tracking metadata of the current transfer-in-progress; and
// b) Interacting with the Archivematica API to start a transfer and perform supporting functions.
class TransferBrowserTransfer {
  constructor($cookies, gettextCatalog, Alert) {
    this.empty_properties();
    this.fetch_processing_configs();
    this.$cookies = $cookies;
    this.gettextCatalog = gettextCatalog;
    this.Alert = Alert;
  }

  empty_properties() {
    this.name = '';
    this.type = 'standard';
    this.accession = '';
    this.access_system_id = '';
    this.components = [];
    this.auto_approve = true;
  }

  // Fetches array of processing configs from API endpoint
  fetch_processing_configs() {
    this.processing_configs = [];
    jQuery.get('/api/processing-configurations/').then(result => {
      this.processing_configs = result.processing_configurations;
    });
  }

  add_component(entry) {
    // Copy the component so we're not mutating the object from the tree
    let component = Object.assign({}, entry);
    // If an ID for the next row has been provided, use it now
    if (this.next_id) {
      component.id = this.next_id;
      delete this.next_id;
    }
    this.components.push(component);
  }

  // Fetches a UUID to be associated with a transfer component.
  // When the API call resolves, the UUID is assigned to the
  // provided object's "id" attribute.
  fetch_id_for(component) {
    return jQuery.get('/transfer/create_metadata_set_uuid/').then(result => {
      component.id = result.uuid;
    });
  }

  // Starts a transfer using this service's current attributes
  // and specified processing configuration.
  start(processing_config) {
    // If this is a zipped bag, then there will be no transfer name;
    // give it a dummy name instead.
    let name = this.name;
    if (this.type === 'zipped bag') {
      name = 'ZippedBag';
    } else if (this.type === 'zipfile') {
      name = 'ZipFile';
    }

    let _self = this;

    let payload = {
      name: name,
      type: _self.type,
      processing_config: processing_config,
      accession: _self.accession,
      access_system_id: _self.access_system_id,
      auto_approve: _self.auto_approve,
    }

    let requests = this.components.map(function(component) {
      payload.path = Base64.encode(`${component.location}:${component.path}`);
      payload.metadata_set_id = component.id || '';

      return jQuery.ajax('/api/v2beta/package/', {
        method: 'POST',
        headers: {'X-CSRFToken': _self.$cookies.get('csrftoken')},
        cache: false,
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        data: JSON.stringify(payload)
      });
    });

    this.Alert.alerts.push({
      'type': 'info',
      'message': this.gettextCatalog.getString(
        'Transfer "{{name}}" started with processing configuration "{{config}}".',
        { name: name, config: processing_config }
      )
    });

    this.empty_properties();

    return $.when(...requests);
  }
}

export default angular.module('services.transfer_browser_transfer', [require('angular-cookies')]).
  service('TransferBrowserTransfer', TransferBrowserTransfer).
  name;
