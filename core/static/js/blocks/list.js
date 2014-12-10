(function($) {
    window.ListBlock = function(opts) {
        /* contents of 'opts':
            definitionPrefix (required)
            childInitializer (optional) - JS initializer function for each child
            templateChildParam (optional) - first param to be passed to childInitializer when adding a new child
        */
        var listMemberTemplate = $('#' + opts.definitionPrefix + '-newmember').text();

        return function(childParams, elementPrefix) {
            var sequence = Sequence({
                'prefix': elementPrefix,
                'onInitializeMember': function(sequenceMember) {
                    /* code to be run on initializing each element, regardless of whether it's part of the
                    initial list or being added dynamically */

                    /* initialise delete button */
                    $('#' + sequenceMember.prefix + '-delete').click(function() {
                        sequenceMember.delete();
                    });
                },
                'onInitializeNewMember': function(sequenceMember) {
                    if (opts.childInitializer) {
                        opts.childInitializer(opts.templateChildParam, sequenceMember.prefix + '-value');
                    }
                },
                'onInitializeInitialMember': function(sequenceMember, index) {
                    if (opts.childInitializer) {
                        opts.childInitializer(childParams[index], sequenceMember.prefix + '-value');
                    }
                }
            });

            /* initialize 'add' button */
            $('#' + elementPrefix + '-add').click(function() {
                sequence.insertMemberAtEnd(listMemberTemplate);
            });
        };
    };
})(jQuery);
