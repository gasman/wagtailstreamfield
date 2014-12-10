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

        function initChild(blockTypeName, childParam, listMemberPrefix) {
            blockOpts = childBlocksByName[blockTypeName];

            /* run childInitializer if one has been supplied */
            if (blockOpts.initializer) {
                /* the child block's own elements have the prefix '{list member prefix}-value' */
                blockOpts.initializer(childParam, listMemberPrefix + '-value');
            }
        }

        return function(childParams, elementPrefix) {
            var sequence = Sequence({
                'prefix': elementPrefix,
                'onInitializeMember': function(sequenceMember) {
                    /* initialize delete button */
                    $('#' + sequenceMember.prefix + '-delete').click(function() {
                        sequenceMember.delete();
                    });

                    /* initialize 'prepend new block' buttons */
                    function initializePrependButton(childBlock) {
                        var template = listMemberTemplates[childBlock.name];
                        $('#' + sequenceMember.prefix + '-add-' + childBlock.name).click(function() {
                            sequenceMember.prependMember(template);
                        });
                    }
                    for (var i = 0; i < opts.childBlocks.length; i++) {
                        initializePrependButton(opts.childBlocks[i]);
                    }
                },
                'onInitializeInitialMember': function(sequenceMember, index) {
                    var blockTypeName = $('#' + sequenceMember.prefix + '-type').val();
                    initChild(blockTypeName, childParams[index], sequenceMember.prefix);
                },
                'onInitializeNewMember': function(sequenceMember) {
                    var blockTypeName = $('#' + sequenceMember.prefix + '-type').val();
                    initChild(blockTypeName, childBlocksByName[blockTypeName].templateInitializerParam, sequenceMember.prefix);
                }
            });

            /* initialize footer menu */
            function initializeAppendButton(childBlock) {
                var template = listMemberTemplates[childBlock.name];
                $('#' + elementPrefix + '-after-add-' + childBlock.name).click(function() {
                    sequence.appendMember(template);
                });
            }
            for (var i = 0; i < opts.childBlocks.length; i++) {
                initializeAppendButton(opts.childBlocks[i]);
            }
        };
    };
})(jQuery);
