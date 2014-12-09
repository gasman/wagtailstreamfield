(function($) {
    window.ListBlock = function(opts) {
        /* contents of 'opts':
            definitionPrefix (required)
            childInitializer (optional) - JS initializer function for each child
            templateChildParam (optional) - first param to be passed to childInitializer when adding a new child
        */
        var listMemberTemplate = $('#' + opts.definitionPrefix + '-childtemplate').text();

        return function(childParams, elementPrefix) {
            var countField = $('#' + elementPrefix + '-count');
            var list = $('#' + elementPrefix + '-list');

            /* initialise children */
            if (opts.childInitializer) {
                for (var i = 0; i < childParams.length; i++) {
                    opts.childInitializer(childParams[i], elementPrefix + '-' + i + '-value');
                }
            }

            /* initialise 'add' button */
            $('#' + elementPrefix + '-add').click(function() {
                var newIndex = parseInt(countField.val(), 10);
                countField.val(newIndex + 1);
                var newListMemberPrefix = elementPrefix + '-' + newIndex;

                var elem = $(listMemberTemplate.replace(/__PREFIX__/g, newListMemberPrefix));
                list.append(elem);
                if (opts.childInitializer) {
                    opts.childInitializer(opts.templateChildParam, newListMemberPrefix + '-value');
                }
            });
        };
    };
})(jQuery);
