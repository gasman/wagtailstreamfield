(function($) {
    window.ListBlock = function(opts) {
        /* contents of 'opts':
            definitionPrefix (required)
            childInitializer (optional) - JS initializer function for each child
            templateChildParam (optional) - first param to be passed to childInitializer when adding a new child
        */
        var listMemberTemplate = $('#' + opts.definitionPrefix + '-newmember').text();

        function initListMember(childParam, listMemberPrefix) {
            /* run childInitializer if one has been supplied */
            if (opts.childInitializer) {
                /* the child block's own elements have the prefix '{list member prefix}-value' */
                opts.childInitializer(childParam, listMemberPrefix + '-value');
            }

            var sequenceMember = SequenceMember(listMemberPrefix);
            /* initialise delete button */
            $('#' + listMemberPrefix + '-delete').click(function() {
                sequenceMember.delete();
            });
        }

        return function(childParams, elementPrefix) {
            var countField = $('#' + elementPrefix + '-count');
            var initialChildCount = parseInt(countField.val(), 10);
            var list = $('#' + elementPrefix + '-list');

            /* initialise children */
            for (var i = 0; i < initialChildCount; i++) {
                initListMember(childParams[i], elementPrefix + '-' + i);
            }

            /* initialise 'add' button */
            $('#' + elementPrefix + '-add').click(function() {
                /* Update the counter and use it to create a prefix for the new list member */
                var newIndex = parseInt(countField.val(), 10);
                countField.val(newIndex + 1);
                var newListMemberPrefix = elementPrefix + '-' + newIndex;

                /* Create the new list member element with a unique ID prefix, and append it to the list */
                var elem = $(listMemberTemplate.replace(/__PREFIX__/g, newListMemberPrefix));
                list.append(elem);
                initListMember(opts.templateChildParam, newListMemberPrefix);
            });
        };
    };
})(jQuery);
