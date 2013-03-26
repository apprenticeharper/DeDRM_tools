// ==UserScript==
// @name        BN-Dload
// @namespace   http://www.mailinator.com/J-man
// @include     https://mynook.barnesandnoble.com/library.html*
// @grant       none
// @version     20121119
// ==/UserScript==

function doIt() {
	if ($('#adl1').length == 0) {
		$('[action$="deleteItem"]').each(function(index) {
			if ($(this).parent().find('[action$="EDSDeliverItem.aspx"]').length == 0) {
				var delid = $(this).find('input').attr('value');
				$(this).after('<span class="vb2"></span><form id="adl' + index + '" action="https://edelivery.barnesandnoble.com/EDS/EDSDeliverItem.aspx" class="download"><input value="' + delid + '" type="hidden" name="delid"><input type="hidden" value="Browser" name="clienttype"><input type="hidden" value="browser" name="deviceinfo"><button class="download "name="download">Alternative Download</button></form>');
			}
		});
		
	}

	setTimeout (function() {
		doIt();
	}, 3000 );
}

doIt();
	
