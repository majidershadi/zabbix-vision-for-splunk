require(['jquery', 'splunkjs/mvc', 'splunkjs/mvc/simplexml/ready!'], function ($, mvc) {
    'use strict';
    var service = mvc.createService({owner: 'nobody', app: 'zabbix_vision'});
    var profileKeys = ['url','verify_tls','allow_http','ca_bundle','client_cert','client_key','tls_min','proxy_url','timeout','retries','max_response_mb','auth_mode','enable_execution','allowed_script_ids','allowed_host_ids'];
    var inputKeys = ['streams','index','interval','lookback','page_size','overlap','settle_delay','window','snapshot_limit','item_ids','history_types','disabled'];
    var profiles = [];
    function values(keys) { var out = {}; keys.forEach(function(k) { out[k] = $('#' + k).val(); }); return out; }
    function show(target, data, error) { $(target).text(typeof data === 'string' ? data : JSON.stringify(data,null,2)).toggleClass('error', !!error); }
    function call(payload, target, after) {
        $('#zbx-setup button').prop('disabled', true);
        show(target, 'Working…', false);
        service.request('zabbix_vision_manager', 'POST', null, null, JSON.stringify(payload), {'Content-Type':'application/json'}, function(err, response) {
            $('#zbx-setup button').prop('disabled', false);
            $('#token, #key_password').val('');
            var data = response && response.data;
            show(target, data || (err ? 'Request failed. Check your permissions and Splunk service status.' : 'Completed.'), !!err);
            if (!err && after) { after(); }
        });
    }
    function refresh() {
        service.get('zabbix_vision_manager', {}, function(err, response) {
            if (err) { show('#connection-result', 'Admin access is required to manage connections.', true); return; }
            profiles = response.data.profiles || [];
            $('#existing').empty().append($('<option>').val('').text('New connection'));
            profiles.forEach(function(p) { $('#existing').append($('<option>').val(p.name).text(p.name)); });
            $('#supported-streams').text('Available: ' + response.data.streams.join(', '));
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
