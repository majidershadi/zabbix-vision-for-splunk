require(['jquery','splunkjs/mvc','splunkjs/mvc/simplexml/ready!'], function($, mvc) {
    'use strict';
    var service = mvc.createService({owner:'nobody',app:'zabbix_vision'});
    $('#execute-script').on('click', function() {
        if ($('#confirmation').val() !== 'EXECUTE') { $('#execution-result').text('Type EXECUTE to confirm this request.'); return; }
        var payload = {action:'execute', name:$('#execution_profile').val(), scriptid:$('#scriptid').val(), hostid:$('#hostid').val(), confirmation:'EXECUTE'};
        $('#execute-script').prop('disabled',true);
        $('#execution-result').text('Execution requested…');
        service.request('zabbix_vision_manager','POST',null,null,JSON.stringify(payload),{'Content-Type':'application/json'},function(err,response) {
            $('#execute-script').prop('disabled',false);
            $('#confirmation').val('');
            $('#execution-result').text(JSON.stringify(response && response.data || {error:'Request failed; check the audit trail before retrying.'},null,2)).toggleClass('error',!!err);
        });
    });
});
