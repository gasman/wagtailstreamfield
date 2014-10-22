(function($) {
    window.Macro = function(templateId, initializer) {
        /* A helper to assist with pasting repeatable blocks of HTML into a page,
        with element IDs rewritten to a specified prefix each time,
        and optionally with Javascript behaviour applied to the block.

        Given a 'template' block somewhere on the page, of the form:
        <script type="text/template" id="my-template">
            <p id="__PREFIX__-paragraph">hello world</p>
        </script>

        a macro can be constructed as:
        myMacro = Macro('my-template', initializer);

        and then pasted at any point into the document using:
        myMacro.paste(containerElement, 'newprefix')

        - here any instances of __PREFIX__ in the template will be replaced by 'newprefix', and
        after insertion into the document, initializer('newprefix') will be called to set up JS
        behaviour for that block.
        */

        var template = $('#' + templateId).text();

        return {
            'paste': function(container, prefix) {
                var elem = $(template.replace(/__PREFIX__/g, prefix));
                $(container).append(elem);
                if (initializer) {
                    initializer(prefix);
                }
            }
        };
    };
})(jQuery);
