/*******************************************************************************
 * Provides functionality for the history web page.
 *
 * This module is intended exclusively for the history page. It contains
 * functions necessary to fetch and manage the historical data for
 * user-executed queries.
 *
 * Functionality Overview:
 * -----------------------
 * - Utilizes the /queries endpoint of the Ragit server to retrieve all
 * available historical data when the history page is loaded.
 *
 * - Stores the retrieved data in memory, enabling users to select and view
 *   any of the available conversations through the front-end interface.
 *
 * Future Improvements:
 * --------------------
 * As the volume of historical data increases, the current approach may lead
 * to memory and performance issues. Future enhancements will focus on making
 * data retrieval and management more dynamic to mitigate these issues.
 ******************************************************************************
 */

// Stores the retrieved queries in memory.
let _historical_queries = null;
let _is_changed = false;
let _current_thumps_up = false;
let _selected_msg_id = null;

// A dict from message id to the corresponding list item that is shown on
// the left side of the screen; used to update it on the fly when the user
// changes the thumps up /down.
let _msg_id_to_list_item = null;

/**
 * Loads the queries and their details calling the API.
 *
 * The function performs the following operations:
 *
 * 1. Iterates over the received data to populate the left-hand query list.
 *    Users can click on an item to view its details on the right side.
 *
 * 2. Constructs a dictionary that maps each message ID to its query details.
 *    This caching mechanism accelerates query lookup in response to user
 *    clicks.
 *
 * Queries are presented in the same order as received from the server,
 * typically sorted by creation time, with the most recent queries displayed
 * first.
 */
function retrieve_queries() {
    document.body.style.cursor = 'wait';
    _historical_queries = {};
    $.ajax({
            url: "/queries",
            type: "GET",
            dataType: 'json',
            success: function (data) {
                document.body.style.cursor = 'default';
                update_queries_from_server(data);
            },
            error: function (request, status, error) {
                document.body.style.cursor = 'default';
                console.error(error)
                alert(request.responseText);
            }
        }
    )
}


/**
 * Updates the history view using the data retrieved from the server.
 */
function update_queries_from_server(data) {
    _historical_queries = {};
    _msg_id_to_list_item = {};

    let first_msg_id = null;
    const questionList = document.getElementById("question-list");
    questionList.innerHTML = '';
    for (let i = 0; i < data.length; i++) {
        const details = data[i];
        const msg_id = details["msg_id"];

        if (first_msg_id === null) {
            first_msg_id = msg_id;
        }

        _historical_queries[msg_id] = details;
        const question = details["question"];
        const li = document.createElement("li");
        li.question = question;
        _msg_id_to_list_item[msg_id] = li;
        add_thumps_emoji_to_label(msg_id, details["thumps_up"]);
        li.addEventListener(
            "click", () => display_query_details(msg_id)
        );
        questionList.appendChild(li);
    }
    if (first_msg_id != null) {
        display_query_details(first_msg_id);
    }
}

function add_thumps_emoji_to_label(msg_id, thumps_up){
    const list_item = _msg_id_to_list_item[msg_id];
    let label = list_item.question;
    if (thumps_up === 1) {
        label = "👍" + label;
        list_item.className = "thumps_up_query";
    } else if (thumps_up === 0) {
        list_item.className = "thumps_down_query";
        label = "👎" + label;
    }
    list_item.innerText = label;
}

/**
 * Paints the thumps up/ down icons.
 *
 * @param thumps_up: 1 if the user has selected thumps up
 *                   0 if the user has selected thumps down
 *                   null if the user has not make a selection yet.
 */
function paint_user_selection_icons(thumps_up) {
    const thumps_up_img = document.getElementById("thumps_up_img");
    const thumps_down_img = document.getElementById("thumps_down_img");

    thumps_up_img.src = "/static/bw-thumbs-up-32.png";
    thumps_down_img.src = "/static/bw-thumbs-down-32.png";

    thumps_down_img.onclick = function () {
        update_is_changed(true, 0);
        paint_user_selection_icons(0);
    }

    thumps_up_img.onclick = function () {
        update_is_changed(true, 1);
        paint_user_selection_icons(1);
    }

    if (thumps_up === 1) {
        thumps_up_img.src = "/static/thumps-up.png";
        thumps_up_img.width = 42;
        thumps_up_img.height = 42;
        thumps_up_img.onclick = function () {

        }
        thumps_down_img.onclick = function () {
            update_is_changed(true, 0);
            paint_user_selection_icons(0);
        }
    } else if (thumps_up === 0) {
        thumps_down_img.src = "/static/thumps-down.png";
        thumps_down_img.width = 42;
        thumps_down_img.height = 42;
        thumps_down_img.onclick = function () {
        }
        thumps_up_img.onclick = function () {
            update_is_changed(true, 1);
            paint_user_selection_icons(1);
        }
    }
}

/**
 * Updates save button and editor display based on changes and thumbs up.
 *
 * @param {boolean} is_changed - Indicates whether changes have been made.
 * @param {number} thumps_up -  0: indicates thumps down 1: thumps up
 *
 */
function update_is_changed(is_changed, thumps_up) {
    _is_changed = is_changed;
    _current_thumps_up = thumps_up;

    if (_is_changed) {
        const btn = document.getElementById("save_changes_btn");
        btn.className = "save_changes_btn_style show_it";
        btn.onclick = save_changes_no_confirm;
    } else {
        const btn = document.getElementById("save_changes_btn");
        btn.className = "save_changes_btn_style hide_it";
    }
    if (thumps_up === 0) {
        const editor = document.getElementById("desired_response_editor");
        editor.className = "editor-container show_it";
    } else {
        const editor = document.getElementById("desired_response_editor");
        editor.className = "editor-container hide_it";
    }

}

/**
 * Marks the desired response as changed and updates the UI accordingly.
 *
 * This function sets the internal `_is_changed` state to true,
 * indicating that the desired response has been modified. It then
 * calls `update_is_changed` to alter the UI elements based on the
 * new change status and the current thumbs up count.
 */
function desired_response_was_changed() {
    _is_changed = true;
    update_is_changed(true, _current_thumps_up);
}

function save_changes_no_confirm(){
    const editor = document.getElementById("correct_response_editor");
    const update_payload = {
        "msg_id": _selected_msg_id,
        "thumps_up": _current_thumps_up,
        "desired_response": editor.value
    }
    document.body.style.cursor = 'wait';

    const msg_id = _selected_msg_id;
    const thumps_up = _current_thumps_up;

    $.ajax({
        url: "/updateuserinteraction",
        type: "PUT",
        data: JSON.stringify(update_payload),
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        success: function (response, status) {
            _is_changed = false;
            update_is_changed(false, thumps_up);
            add_thumps_emoji_to_label(msg_id, thumps_up);
            _historical_queries[msg_id]["thumps_up"] = thumps_up;
            document.body.style.cursor = 'default';
        },
        error: function (request, status, error) {
            document.body.style.cursor = 'default';
            console.error(request.responseText);
            alert(request.responseText);
        }
    });
}


/**
 * Should be called when the used clicks on a query to display its details.
 */
function display_query_details(msg_id) {
    if (_is_changed && confirm('Do you want to save your changes?')) {
        save_changes_no_confirm();
    }

    $("#delete_query_btn").removeClass().addClass("action_button disabled");
    const details = _historical_queries[msg_id];

    document.getElementById("query").innerText = details.question;
    document.getElementById("response").innerText = details.response;

    const br = document.createElement("br")
    document.getElementById("response").appendChild(br);

    //document.getElementById("response").appendChild(create_audio_tag(msg_id));

    paint_user_selection_icons(details["thumps_up"])
    document.getElementById("response_label").innerText = "Response";

    const desired_response_text_box = document.getElementById("correct_response_editor");
    desired_response_text_box.innerText = details.desired_response;

    document.getElementById("chunks").innerHTML = '';
    details.matches.forEach(chunk => {
            const chunks_container = document.getElementById("chunks");

            const meta_container = document.createElement("div");
            meta_container.className = "meta_container_div"
            chunks_container.appendChild(meta_container);

            meta_container.appendChild(
                display_value_in_rect(chunk["distance"])
            );

            meta_container.appendChild(
                display_document_link(chunk["source"])
            )

            const page = chunk["page"];
            if (page != null) {
                meta_container.appendChild(
                    display_value_in_span(`page: ${page}`)
                )
            }

            const p = document.createElement("p");
            p.innerText = chunk["txt"];
            chunks_container.appendChild(p);

            const hr = document.createElement("hr");
            chunks_container.appendChild(hr);
        }
    )
    ;
    document.getElementById("prompt").innerText = details.prompt;

    const how_long_before = time_ago(details.received_at);

    $("#time_ago_span").text(`asked ${how_long_before}`);
    $("#temperature_span").text(`temperature ${details.temperature}`);
    $("#max_tokens_span").text(`max tokens ${details.max_tokens}`);
    $("#matches_count_span").text(`matches ${details.count_matches}`);


    $("#delete_query_btn").removeClass().addClass("action_button");

    $("#delete_query_btn").off("click");

    $("#delete_query_btn").click(function () {
        const userConfirmed = confirm(
            'Are you sure you want to delete the active query information?'
        );

        if (userConfirmed) {
            delete_query(msg_id);
        }
    })

    _selected_msg_id = msg_id;

    update_is_changed(false, details["thumps_up"]);
}

/**
 * Deletes a Query from the database using the message id.
 */
function delete_query(msg_id) {
    document.body.style.cursor = 'wait';
    const url = `/queries/${msg_id}`;
    $.ajax({
            url: url,
            type: "DELETE",
            dataType: 'json',
            success: function (data) {
                document.body.style.cursor = 'default';
                retrieve_queries()
            },
            error: function (request, status, error) {
                document.body.style.cursor = 'default';
                console.error(error)
                alert(request.responseText);
            }
        }
    )
}


/**
 * Converts a datetime string to a human-readable relative time description.
 *
 * This function receives a datetime string, calculates the difference from
 * the current time, and returns a string describing how long ago the datetime
 * was, such as "now", "3 minutes ago", "2 days ago", "2 weeks ago", etc.
 *
 * @param {string} datetimeStr - The datetime string in ISO format
 *  (e.g., '2024-10-06T14:20:51.650732').
 *
 * @return {string} A human-readable string indicating the relative time
 *   since the datetime.
 */
function time_ago(datetimeStr) {
    const now = new Date();
    const pastDate = new Date(datetimeStr);
    const diffInSeconds = Math.floor((now - pastDate) / 1000);

    const secondsInMinute = 60;
    const secondsInHour = 3600;
    const secondsInDay = 86400;
    const secondsInWeek = 604800;
    const secondsInMonth = 2592000; // Roughly 30 days
    const secondsInYear = 31536000; // Roughly 365 days

    if (diffInSeconds < secondsInMinute) {
        return "now";
    } else if (diffInSeconds < secondsInHour) {
        const minutes = Math.floor(diffInSeconds / secondsInMinute);
        return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < secondsInDay) {
        const hours = Math.floor(diffInSeconds / secondsInHour);
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < secondsInWeek) {
        const days = Math.floor(diffInSeconds / secondsInDay);
        return `${days} day${days > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < secondsInMonth) {
        const weeks = Math.floor(diffInSeconds / secondsInWeek);
        return `${weeks} week${weeks > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < secondsInYear) {
        const months = Math.floor(diffInSeconds / secondsInMonth);
        return `${months} month${months > 1 ? 's' : ''} ago`;
    } else {
        const years = Math.floor(diffInSeconds / secondsInYear);
        return `${years} year${years > 1 ? 's' : ''} ago`;
    }
}


/**
 * Create a span element to wrap the label and value
 */
function display_value_in_span(value) {
    const span = document.createElement('span');
    span.className = "value_container";
    span.textContent = value;
    return span;
}

/**
 * Displays the link to the document. When clicked it will open a modal window.
 *
 * @param {string} filepath - The relative file path to display in the title.
 */
function display_document_link(filepath) {
    const span = document.createElement('span');
    span.className = "value_container";
    const link = document.createElement("a");
    link.href = "#";
    link.onclick = function () {
        // Called when the user clicks on document link.
        // Evaluate the document type.
        const index = filepath.lastIndexOf('.');
        const file_ext = filepath.slice(index) ? filepath.slice(index) : "";
        let url = "/document/" + filepath;

        // Call the applicable function to display the document.
        if (file_ext === ".pdf") {
            show_pdf_modal_dialog(url, filepath);
        } else if (file_ext === ".docx") {
            alert(`File type ${docx} is not supported`)
        } else {
            show_modal_dialog(url, filepath);
        }
    }
    link.innerText = filepath;
    span.appendChild(link);
    return span;
}

/**
 * Displays a numeric value in a rectangle (up to two decimals).
 *
 */
function display_value_in_rect(value) {
    const span = document.createElement("span");
    span.className = "value_rect";
    span.textContent = value.toFixed(2);
    return span;
}

/**
 * Displays a pdf in a modal dialog.
 *
 * @param {string} doc_link - The link to the document to display.
 * @param {string} filepath - The relative file path to display in the title.
 *
 */
function show_pdf_modal_dialog(doc_link, filepath) {
    const dialog = document.getElementById('editorDialog');
    dialog.innerHTML = '';
    dialog.className = "modal_editor";
    const div = document.createElement("div");
    div.id = "modal_editor";

    // Add the top line div (to store close button and title).
    const doc_info_div = document.createElement("div");
    dialog.appendChild(doc_info_div);
    doc_info_div.className = "title"

    // Adds the close button.
    const close_button = document.createElement("button");
    close_button.innerText = "X";
    close_button.onclick = function () {
        const dialog = document.getElementById('editorDialog');
        dialog.close();
    }
    doc_info_div.appendChild(close_button);

    // Adds the title for the modal window.
    const title = document.createElement("span");
    title.innerText = filepath;
    doc_info_div.appendChild(title);

    const embed = document.createElement("embed");
    embed.type = "application/pdf";
    embed.className = "pdf-frame";
    embed.src = doc_link;
    dialog.appendChild(embed);
    dialog.showModal();
}

/**
 * Displays a modal dialog for text loaded using a link to the server.
 *
 * @param {string} doc_link - The link to the document to display.
 * @param {string} filepath - The relative file path to display in the title.
 */
function show_modal_dialog(doc_link, filepath) {
    const dialog = document.getElementById('editorDialog');
    dialog.innerHTML = '';
    dialog.className = "modal_editor";

    // Add the top line div (to store close button and title).
    const doc_info_div = document.createElement("div");
    dialog.appendChild(doc_info_div);
    doc_info_div.className = "title"

    // Adds the close button.
    const close_button = document.createElement("button");
    close_button.innerText = "X";
    close_button.onclick = function () {
        const dialog = document.getElementById('editorDialog');
        dialog.close();
    }
    doc_info_div.appendChild(close_button);

    // Adds the title for the modal window.
    const title = document.createElement("span");
    title.innerText = filepath;
    doc_info_div.appendChild(title);

    // Add the frame where the document will be displayed.
    const frame = document.createElement("iframe");
    frame.src = doc_link;
    frame.title = filepath;
    dialog.appendChild(frame);
    dialog.showModal();
}
