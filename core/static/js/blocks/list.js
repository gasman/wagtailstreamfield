(function($) {
    /* ListBlock may be constructed with or without a childInitializer.
    If it's constructed without one, this means that the child block doesn't have any JS
    behaviour, and we only have to set up the dynamic list behaviour.
    */
    window.ListBlock = function(definitionPrefix, childInitializer) {
        var childMacro = Macro(definitionPrefix + '-template', childInitializer);

        return function(elementPrefix) {
            var countField = $('#' + elementPrefix + '-count');
            var list = $('#' + elementPrefix + '-list');

            if (childInitializer) {
                /* initialise children */
                var count = parseInt(countField.val(), 10);
                for (var i = 0; i < count; i++) {
                    childInitializer(elementPrefix + '-' + i);
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
