/* Operations on a sequence of items, common to both ListBlock and StreamBlock.
These assume the presence of a container element named "{prefix}-container" for each list item, and
certain hidden fields such as "{prefix}-deleted" as defined in sequence_member.html, but make no assumptions
about layout or visible controls within the block. 
For example, they don't assume the presence of a 'delete' button - it's up to the specific subclass
(list.js / stream.js) to attach this to the SequenceMember.delete method.
*/
(function($) {
    window.SequenceMember = function(elementPrefix) {
        var self = {};
        var container = $('#' + elementPrefix + '-container');

        self.delete = function() {
            /* set this list member's hidden 'deleted' flag to true */
            $('#' + elementPrefix + '-deleted').val('1');
            /* hide the list item */
            $('#' + elementPrefix + '-container').fadeOut();
        };

        return self;
    };
})(jQuery);
