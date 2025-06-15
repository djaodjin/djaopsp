// function used to measure performance of external redirects

(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD. Register as an anonymous module.
        define(['exports'], factory);
    } else if (typeof exports === 'object' && typeof exports.nodeName !== 'string') {
        // CommonJS
        factory(exports);
    } else {
        // Browser true globals added to `window`.
        factory(root);
        // If we want to put the exports in a namespace, use the following line
        // instead.
        // factory((root.djResources = {}));
    }
}(typeof self !== 'undefined' ? self : this, function (exports) {

function logExternalRedirect(event, redirectTo, logExternalRedirectUrl) {
    event.preventDefault();
    if( redirectTo ) {
        if( logExternalRedirectUrl ) {
            const csrfTokenElement = event.target.querySelector(
                '[name="csrfmiddlewaretoken"]')
            let headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfTokenElement.value,
            }
            fetch(logExternalRedirectUrl, {
                method: "POST",
                headers: headers,
                body: JSON.stringify({'redirect_to': redirectTo})
            });
        }
        window.open(redirectTo, '_blank');
    }
    return 0;
}

    // attach properties to the exports object to define
    // the exported module properties.
    exports.logExternalRedirect = logExternalRedirect;

}));
