require(['jquery', 'splunkjs/mvc', 'splunkjs/mvc/simplexml/ready!'], function ($, mvc) {
    'use strict';
    var service = mvc.createService({owner: 'nobody', app: 'zabbix_vision'});
    var profileKeys = ['url','verify_tls','allow_http','ca_bundle','client_cert','client_key','tls_min','proxy_url','timeout','retries','max_response_mb','auth_mode','enable_execution','allowed_script_ids','allowed_host_ids'];
    var inputKeys = ['streams','index','interval','lookback','page_size','overlap','settle_delay','window','snapshot_limit','item_ids','history_types','userparameter_item_ids','disabled'];
    var profiles = [];
    function values(keys) { var out = {}; keys.forEach(function(k) { out[k] = $('#' + k).val(); }); return out; }
    function show(target, data, error) { $(target).text(typeof data === 'string' ? data : JSON.stringify(data,null,2)).toggleClass('error', !!error); }
    function jsonObject(data) {
        if (typeof data === 'string') {
            try { data = JSON.parse(data); } catch (e) { return null; }
        }
        return data && typeof data === 'object' ? data : null;
    }
    function appError(data) {
        data = jsonObject(data);
        if (data && data.source === 'zabbix_vision' && typeof data.error === 'string') {
            return data.error;
        }
        return null;
    }
    function requestError(err) {
        var data = jsonObject(err.data || err.responseJSON || err.responseText);
        var message = appError(data);
        // Some Splunk Web versions wrap the handler's reply in a REST message.
        if (!message && data && Array.isArray(data.messages)) {
            data.messages.some(function(item) {
                message = item && appError(item.text);
                return !!message;
            });
        }
        if (message) { return message; }
        var status = Number(err.status || (err.response && err.response.status));
        if (status === 401) { return 'Your Splunk session has expired. Sign in again and reload this page.'; }
        if (status === 403) { return 'Splunk denied this setup request (HTTP 403). Use an administrator session.'; }
        if (status === 404) { return 'The setup endpoint was not found (HTTP 404). Verify the app is enabled and restart Splunk after installation.'; }
        if (status >= 400 && status <= 599) {
            return 'Splunk returned HTTP ' + status + ' without a setup error message. Reload this page and check splunkd.log or web_service.log if the problem persists.';
        }
        return 'Splunk did not return a setup response. Reload this page and try again.';
    }
    function call(payload, target, after) {
        $('#zbx-setup button').prop('disabled', true);
        show(target, 'Working…', false);
        service.request('zabbix_vision_manager', 'POST', {output_mode: 'json'}, null, JSON.stringify(payload), {'Content-Type':'application/json'}, function(err, response) {
            $('#zbx-setup button').prop('disabled', false);
            $('#token, #key_password').val('');
            if (err) { show(target, requestError(err), true); return; }
            var data = jsonObject(response && response.data);
            if (!data || !Object.keys(data).length) {
                show(target, 'Splunk returned an unexpected setup response. Reload this page and check Existing connection before retrying.', true);
                return;
            }
            show(target, data, false);
            if (after) { after(); }
        });
    }
    function refresh() {
        service.get('zabbix_vision_manager', {}, function(err, response) {
            if (err) { show('#connection-result', requestError(err), true); return; }
            var data = jsonObject(response && response.data);
            if (!data || !Array.isArray(data.profiles) || !Array.isArray(data.streams)) {
                show('#connection-result', 'Splunk returned an unexpected connections list. Reload this page and try again.', true);
                return;
            }
            profiles = data.profiles;
            $('#existing').empty().append($('<option>').val('').text('New connection'));
            profiles.forEach(function(p) { $('#existing').append($('<option>').val(p.name).text(p.name)); });
            $('#supported-streams').text('Available: ' + data.streams.join(', '));
        });
    }
    $('#existing').on('change', function() {
        var selected = profiles.find(function(p) { return p.name === $('#existing').val(); });
        $('#token, #key_password').val('');
        if (!selected) { $('#profile_name').val(''); return; }
        $('#profile_name').val(selected.name);
        profileKeys.forEach(function(k) { $('#' + k).val(selected.settings[k]); });
    });
    $('#save-profile').on('click', function() { call({action:'save', name:$('#profile_name').val(), settings:values(profileKeys), token:$('#token').val(), key_password:$('#key_password').val()}, '#connection-result', refresh); });
    $('#test-profile').on('click', function() { call({action:'test', name:$('#profile_name').val()}, '#connection-result'); });
    $('#save-input').on('click', function() { var settings = values(inputKeys); settings.profile = $('#profile_name').val(); call({action:'input', name:$('#input_name').val(), settings:settings}, '#input-result'); });
    refresh();
});
