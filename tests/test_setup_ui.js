const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const setup = fs.readFileSync(path.join(__dirname, '..', 'zabbix_vision/appserver/static/setup.js'), 'utf8');

function saveConnection(err, response) {
    const fields = new Map();
    const events = new Map();
    let reads = 0;

    function jquery(selector) {
        if (!fields.has(selector)) {
            fields.set(selector, {
                value: '',
                val(value) { if (arguments.length === 0) { return this.value; } this.value = value; return this; },
                text(value) { this.message = value; return this; },
                toggleClass(name, enabled) { this.hasError = enabled; return this; },
                prop(name, value) { this[name] = value; return this; },
                on(event, callback) { events.set(selector + ':' + event, callback); return this; },
                empty() { return this; },
                append() { return this; }
            });
        }
        return fields.get(selector);
    }

    const service = {
        get(endpoint, query, callback) {
            reads += 1;
            callback(null, {data: {profiles: [], streams: []}});
        },
        request(endpoint, method, query, post, body, headers, callback) {
            assert.equal(endpoint, 'zabbix_vision_manager');
            assert.equal(method, 'POST');
            assert.equal(JSON.parse(body).action, 'save');
            callback(err, response);
        }
    };

    vm.runInNewContext(setup, {
        require(dependencies, init) {
            init(jquery, {createService() { return service; }});
        }
    });
    events.get('#save-profile:click')();
    assert.equal(jquery('#zbx-setup button').disabled, false);
    return {result: jquery('#connection-result'), reads};
}

const validation = {source: 'zabbix_vision', error: 'Enter an API token for a new connection'};
const direct = saveConnection({status: 400, data: validation});
assert.equal(direct.result.message, validation.error);
assert.equal(direct.result.hasError, true);
assert.equal(direct.reads, 1);

const wrapped = saveConnection({
    status: 400,
    data: JSON.stringify({messages: [{type: 'ERROR', text: JSON.stringify(validation)}]})
});
assert.equal(wrapped.result.message, validation.error);

const proxy = saveConnection({status: 400, data: '<html>reflected fixture-token</html>'});
assert.match(proxy.result.message, /HTTP 400/);
assert.doesNotMatch(proxy.result.message, /fixture-token/);

const saved = saveConnection(null, {data: {saved: 'prod', warning: 'Connection saved. Setup status failed.'}});
assert.equal(saved.result.hasError, false);
assert.match(saved.result.message, /Connection saved/);
assert.equal(saved.reads, 2);
console.log('Setup UI: app errors, proxy errors, and saved-with-warning response passed.');
