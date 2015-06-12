TA_RATE = 14.49; // average time spent by a TA on a student

queue = [];
newRequests = 0;
titleText = "COS Help Queue";
pageActive = true;

onOpen = function() {
    queue = JSON.parse(initial_queue);
    refreshQueue();
}

onMessage = function(m) {
    console.log("incoming message");
    // this is a bit of a hack, but for now we'll ignore the
    // race condition and just say that only if the queue grows,
    // there's new people in it
    var msg = JSON.parse(m.data);
    var obj = JSON.parse(msg.data);
    console.log(msg.type);
    if (msg.type == "queue")
    {
        active_tas = msg.active_tas;
        var newQueue = obj;
        if (newQueue.length > queue.length && !pageActive)
        {
            newRequests += newQueue.length - queue.length;
            if (newRequests == 1)
                document.title = newRequests + " New Request!";
            else
                document.title = newRequests + " New Requests!";
        }
        queue = newQueue;
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
    var table = $("#table-queue");
    table.find("tr:gt(0)").remove();
    var header = $("#table-header");
    var curr_queue = $("#table-header").nextAll();
    var button_template = $("#queue-btn-template");
    for (var i = 0; i < queue.length; i++) {
        var new_row = header.clone();
	
	/* NOTE: If you want to add a new type of column, make sure
           to also update the header in the template (since a new row
           is created by cloning the header row. */

	new_row.children(".hr-number").html(i + 1)
        new_row.children(".hr-name").html(queue[i].name);
        new_row.children(".hr-email").html(queue[i].email);
        if (is_ta || queue[i].email == curr_user)
        {
            new_row.children(".hr-action").html(button_template.html());
        }
        else new_row.children(".hr-action").html("");
        if (is_ta)
        {
            new_row.children(".hr-course").html(queue[i].course);
            new_row.children(".hr-msg").html(queue[i].help_msg);
        }
	new_row.children(".hr-id").html(queue[i].full_id);
        table.append(new_row);
    }
    update_wait();
}

update_wait = function () {
    if (active_tas < 2) active_tas = 2;
    var queue_pos = queue.length; // default to end if not in the queue
    for (var i = 0; i < queue.length; i++) {
        if (queue[i].email == curr_user)
        {
            queue_pos = i;
            break;
        }
    }

    var wait_time = Math.round(TA_RATE / active_tas * queue_pos);
    if (queue_pos <= 2) wait_time = Math.min(5, wait_time);

    if (queue_pos == queue.length)
        $("#wait_text").text("Expected Wait Time from the End of the Queue: ");
    else
        $("#wait_text").text("Your Expected Wait Time: ");

    if (wait_time <= 5)
        $("#wait_time").text("< 5 minutes").removeClass().addClass("label label-success");
    else if (wait_time <= 15)
        $("#wait_time").text(wait_time + " minutes").removeClass().addClass("label label-success");
    else if (wait_time <= 30)
        $("#wait_time").text(wait_time + " minutes").removeClass().addClass("label label-warning");
    else if (wait_time <= 45)
        $("#wait_time").text(wait_time + " minutes").removeClass().addClass("label label-danger");
    else
        $("#wait_time").text("> 45 minutes").removeClass().addClass("label label-danger");
}

getRowParams = function(e, btn) {
    
    // server picks up user name (so no need to pass it)
    var email = $(btn).parent().siblings(".hr-email").text();
    var full_id = $(btn).parent().siblings(".hr-id").text() || "";
    
    return { email   : email,
	     full_id : full_id };
}

closeRequest = function(e) {
    e.preventDefault();
    var row_params = getRowParams(e, this);
    $.post("/mark-helped", row_params);
    return false;
}

cancelRequest = function(e) {
    console.log("cancel");
    e.preventDefault();
    var row_params = getRowParams(e, this);
    $.post("/cancel", row_params);
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
    for (var i = 0; i < queue.length; i++) {
        if (queue[i].email == usr) return true;
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
    $("#table-queue").on("click", ".close-req", handler=closeRequest);
    $("#table-queue").on("click", ".cancel-req", handler=cancelRequest);
    $("#form-submit").on("submit", handler=enterQueue);
    $("#btn-confirm-clear").on("click", handler=clearQueue);
    $(window).on("blur focus", viewChange);
    console.log(curr_user)
    console.log(is_ta)
    console.log(initial_queue)
})



