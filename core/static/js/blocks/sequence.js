/* Operations on a sequence of items, common to both ListBlock and StreamBlock.
These assume the presence of a container element named "{prefix}-container" for each list item, and
certain hidden fields such as "{prefix}-deleted" as defined in sequence_member.html, but make no assumptions
about layout or visible controls within the block. 
For example, they don't assume the presence of a 'delete' button - it's up to the specific subclass
(list.js / stream.js) to attach this to the SequenceMember.delete method.
*/
(function($) {
    window.SequenceMember = function(prefix) {
        var self = {};
        self.prefix = prefix;
        var container = $('#' + self.prefix + '-container');
        var indexField = $('#' + self.prefix + '-order');

        self.delete = function() {
            /* set this list member's hidden 'deleted' flag to true */
            $('#' + self.prefix + '-deleted').val('1');
            /* hide the list item */
            $('#' + self.prefix + '-container').fadeOut();
        };
        self.getIndex = function() {
            return parseInt(indexField.val(), 10);
        };
        self.setIndex = function(i) {
            indexField.val(i);
        };

        return self;
    };
    window.Sequence = function(opts) {
        var self = {};
        var list = $('#' + opts.prefix + '-list');
        var countField = $('#' + opts.prefix + '-count');
        var members = [];

        self.getCount = function() {
            return parseInt(countField.val(), 10);
        };
        self.appendMember = function(template) {
            /* Update the counter and use it to create a prefix for the new list member */
            var newIndex = self.getCount();
            countField.val(newIndex + 1);
            var newMemberPrefix = opts.prefix + '-' + newIndex;

            /* Create the new list member element with a unique ID prefix, and append it to the list */
            var elem = $(template.replace(/__PREFIX__/g, newMemberPrefix));
            list.append(elem);
            var sequenceMember = SequenceMember(newMemberPrefix);
            members.push(sequenceMember);
            sequenceMember.setIndex(newIndex);

            if (opts.onInitializeMember) {
                opts.onInitializeMember(sequenceMember, newMemberPrefix);
            }
            if (opts.onInitializeNewMember) {
                opts.onInitializeNewMember(sequenceMember, newMemberPrefix);
            }

            return sequenceMember;
        };

        for (var i = 0; i < self.getCount(); i++) {
            var memberPrefix = opts.prefix + '-' + i;
            var sequenceMember = SequenceMember(memberPrefix);
            members[i] = sequenceMember;
            if (opts.onInitializeMember) {
                opts.onInitializeMember(sequenceMember, memberPrefix);
            }
            if (opts.onInitializeInitialMember) {
                opts.onInitializeInitialMember(sequenceMember, memberPrefix, i);
            }
        }

        return self;
    };
})(jQuery);
