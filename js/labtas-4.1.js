TA_RATE = 14.49; // average time spent by a TA on a student

queues = [];
newRequests = 0;
titleText = "COS Help Queue";
pageActive = true;


var entityMap = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': '&quot;',
    "'": '&#39;',
    "/": '&#x2F;'
};

function escapeHTML(string) {
    return String(string).replace(/[&<>"'\/]/g, function (s) {
        return entityMap[s];
    });
}

onOpen = function() {
    queues = initial_queues;
    for (var i = 0; i < queues.length; i++) {
        var qid = queues[i]['id'];
        $("#table-queue-" + qid).on("click", ".close-req", handler=closeRequest);
        $("#table-queue-" + qid).on("click", ".cancel-req", handler=cancelRequest);
    }
    refreshQueue();
}

onMessage = function(m) {
    console.log("incoming message");
    // this is a bit of a hack, but for now we'll ignore the
    // race condition and just say that only if the total queue grows,
    // there's new people in it
    var msg = JSON.parse(m.data);
    var obj = JSON.parse(msg.data);
    console.log(msg.type);
    console.log(msg.data);

    if (msg.type == "queue")
    {
        var newQueues = obj;

        var old_length = 0;
        var new_length = 0;
        for (var i = 0; i < newQueues.length; i++) {
            new_length += newQueues[i].length;
        }
        for (var i = 0; i < queues.length; i++){
            old_length += queues[i].length;
        }

        if (new_length > old_length && !pageActive)
        {
            newRequests += new_length - old_length;
            if (newRequests == 1)
                document.title = newRequests + " New Request!";
            else
                document.title = newRequests + " New Requests!";
        }
        queues = newQueues;
        refreshQueue();
    }
    else if (msg.type == "request_ack")
    {
        params = $.param({'name': obj.name, 'img': obj.img});
        $('#ack-modal').modal({remote: '/ack-modal?' + params});
        console.log(obj.img);
    }
}

refreshQueue = function() {

    console.log(is_ta);
    console.log(queues);

    for (var j = 0; j < queues.length; j++) {

        var qid = queues[j].id;
        var table = $("#table-queue-" + qid);
        table.find("tr:gt(0)").remove();
        var header = $("#table-header-" + qid);
        var curr_queue = $("#table-header-" + qid).nextAll();
        var button_template = $("#queue-btn-template");

        var q = queues[j]['queue']

        for (var i = 0; i < q.length; i++) {
            var new_row = header.clone();
            new_row.children(".hr-number").html(i + 1)
            new_row.children(".hr-name").html(escapeHTML(q[i].name));
            new_row.children(".hr-email").html(escapeHTML(q[i].email));
            if (is_ta || q[i].email == curr_user)
            {
                new_row.children(".hr-action").html(button_template.html());
            }
            else new_row.children(".hr-action").html("");
            if (is_ta)
            {
                new_row.children(".hr-course").html(escapeHTML(q[i].course));
                new_row.children(".hr-msg").html(escapeHTML(q[i].help_msg));
            }
            // Auto-focus tab w/ current user's request.
            if (q[i].email == curr_user) {
                $('#queue-tab a[href="#' + qid + '"]').tab('show');
            }
            table.append(new_row);
        }
    }
    update_wait();
}

update_wait = function () {

    for (var l = 0; l < queues.length; l++) {

        var q = queues[l]['queue'];
        var qid = queues[l]['id'];
        var active_tas = queues[l]['num_tas'];
        if (active_tas < 1) active_tas = 1;

        var queue_pos = q.length; // default to end if not in the queue
        for (var i = 0; i < q.length; i++) {
            if (q[i].email == curr_user)
            {
                queue_pos = i;
                break;
            }
        }

        var wait_time = Math.round(TA_RATE / active_tas * queue_pos);

        if (queue_pos <= 2) wait_time = Math.min(5, wait_time);

        if (queue_pos == q.length)
            $("#wait_text_" + qid).text("Expected Wait Time from the End of the Queue: ");
        else
            $("#wait_text_" + qid).text("Your Expected Wait Time: ");

        if (wait_time <= 5)
            $("#wait_time_" + qid).text("< 5 minutes").removeClass().addClass("label label-success");
        else if (wait_time <= 15)
            $("#wait_time_" + qid).text(wait_time + " minutes").removeClass().addClass("label label-success");
        else if (wait_time <= 30)
            $("#wait_time_" + qid).text(wait_time + " minutes").removeClass().addClass("label label-warning");
        else if (wait_time <= 45)
            $("#wait_time_" + qid).text(wait_time + " minutes").removeClass().addClass("label label-danger");
        else
            $("#wait_time_" + qid).text("> 45 minutes").removeClass().addClass("label label-danger");
    }
}

closeRequest = function(e) {
    e.preventDefault();
    var email = $(this).parent().siblings(".hr-email").text();
    $.post("/mark-helped", {email: email}); // server picks up user name
    return false;
}

cancelRequest = function(e) {
    console.log("cancel");
    e.preventDefault();
    var email = $(this).parent().siblings(".hr-email").text();
    $.post("/cancel", {email: email}); // server picks up user name
    return false;
}

clearQueue = function(e) {
    console.log("clear queue");
    e.preventDefault();
    $.post("/clear-queue");
}

queueError = function() {
    console.log("error occurred");
    alert("Error entering queue! Please try again.");
}

enterQueue = function(e) {
    console.log("enter queue");
    e.preventDefault();
    if (isInQueue(curr_user))
    {
        alert("You're already in the queue!");
        return false;
    }
    // otherwise post to the server adding them to the queue
    $.post("/add", $(this).serialize());
    $(this).find("[name='name']").val("");
    $(this).find("[name='help_msg']").val("");
    return false;
}

viewChange = function(e) {
    var prevType = $(this).data("prevType");
    if (prevType != e.type) // reduce double fire
    {
        switch (e.type)
        {
            case "blur":
                pageActive = false;
                break;
            case "focus":
                newRequests = 0;
                document.title = titleText;
                break;
        }
    }
}

isInQueue = function(usr) {
    for (var i = 0; i < queues.length; i++) {
        for (var j = 0; j < queues[i]['queue'].length; j++) {
            if (queues[i]['queue'][j].email == usr) {
                return true;
            }
        }
    }
    return false;
}

// The ready function, do bindings/manipulation here
$(document).ready(function() {
    console.log(token);
    channel = new goog.appengine.Channel(token);
    var handler = {
        'onopen': onOpen,
        'onmessage': onMessage,
        'onerror': function() {},
        'onclose': function() {}
        };
    var socket = channel.open(handler)
    $("#form-submit").on("submit", handler=enterQueue);
    $("#btn-confirm-clear").on("click", handler=clearQueue);
    $(window).on("blur focus", viewChange);
    console.log(curr_user)
    console.log(is_ta)
})



