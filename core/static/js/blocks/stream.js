(function($) {
    window.StreamBlock = function(opts) {
        /* Fetch the HTML template strings to be used when adding a new block of each type.
        Also reorganise the opts.childBlocks list into a lookup by name
        */
        var listMemberTemplates = {};
        var childBlocksByName = {};
        for (var i = 0; i < opts.childBlocks.length; i++) {
            var childBlock = opts.childBlocks[i];
            childBlocksByName[childBlock.name] = childBlock;
            var template = $('#' + opts.definitionPrefix + '-newmember-' + childBlock.name).text();
            listMemberTemplates[childBlock.name] = template;
        }

        function initListMember(blockTypeName, childParam, listMemberPrefix) {
            blockOpts = childBlocksByName[blockTypeName];

            /* run childInitializer if one has been supplied */
            if (blockOpts.initializer) {
                /* the child block's own elements have the prefix '{list member prefix}-value' */
                blockOpts.initializer(childParam, listMemberPrefix + '-value');
            }

            /* initialise delete button */
            $('#' + listMemberPrefix + '-delete').click(function() {
                /* set this list member's hidden 'deleted' flag to true */
                $('#' + listMemberPrefix + '-deleted').val('1');
                /* hide the list item */
                $('#' + listMemberPrefix + '-container').fadeOut();
            });
        }

        return function(childParams, elementPrefix) {
            var countField = $('#' + elementPrefix + '-count');
            var list = $('#' + elementPrefix + '-list');

            /* initialise children */
            for (var i = 0; i < childParams.length; i++) {
                var listMemberPrefix = elementPrefix + '-' + i;
                var blockTypeName = $('#' + listMemberPrefix + '-type').val();
                initListMember(blockTypeName, childParams[i], listMemberPrefix);
            }
        };
    };
})(jQuery);
