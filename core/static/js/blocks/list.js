(function($) {
    window.ListBlock = function(opts) {
        /* contents of 'opts':
            definitionPrefix (required)
            childInitializer (optional) - JS initializer function for each child
            templateChildParam (optional) - first param to be passed to childInitializer when adding a new child
        */
        var childMacro;
        if (opts.childInitializer) {
            childMacro = Macro(opts.definitionPrefix + '-template', function(prefix) {
                opts.childInitializer(opts.templateChildParam, prefix);
            });
        } else {
            childMacro = Macro(opts.definitionPrefix + '-template');
        }

        return function(childParams, elementPrefix) {
            var countField = $('#' + elementPrefix + '-count');
            var list = $('#' + elementPrefix + '-list');

            /* initialise children */
            if (opts.childInitializer) {
                for (var i = 0; i < childParams.length; i++) {
                    opts.childInitializer(childParams[i], elementPrefix + '-' + i);
                }
            }

            /* initialise 'add' button */
            $('#' + elementPrefix + '-add').click(function() {
                var newIndex = parseInt(countField.val(), 10);
                countField.val(newIndex + 1);
                var li = $('<li></li>');
                list.append(li);
                childMacro.paste(li, elementPrefix + '-' + newIndex);
            });
        };
    };
})(jQuery);
