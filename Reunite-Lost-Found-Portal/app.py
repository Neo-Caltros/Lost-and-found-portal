import os

from flask import Flask, flash, redirect, render_template, request, url_for

from portal_storage import (
    add_claim,
    create_item,
    get_categories,
    get_item,
    get_portal_stats,
    get_recent_items,
    initialize_portal,
    list_items,
)


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")


@app.before_request
def boot_storage():
    initialize_portal()


def form_value(name):
    return request.form.get(name, "").strip()


@app.route("/")
def home():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    item_type = request.args.get("type", "").strip()
    return render_template(
        "home.html",
        items=list_items(query=query, category=category, item_type=item_type, limit=12),
        recent_items=get_recent_items(limit=3),
        stats=get_portal_stats(),
        categories=get_categories(),
        query=query,
        selected_category=category,
        selected_type=item_type,
    )


@app.route("/browse")
def browse():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    item_type = request.args.get("type", "").strip()
    return render_template(
        "browse.html",
        items=list_items(query=query, category=category, item_type=item_type, limit=100),
        categories=get_categories(),
        query=query,
        selected_category=category,
        selected_type=item_type,
    )


@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        values = {
            "item_type": form_value("item_type"),
            "title": form_value("title"),
            "category": form_value("category"),
            "description": form_value("description"),
            "location": form_value("location"),
            "date_reported": form_value("date_reported"),
            "color": form_value("color"),
            "contact_name": form_value("contact_name"),
            "contact_email": form_value("contact_email"),
            "contact_phone": form_value("contact_phone"),
        }
        required = ("item_type", "title", "category", "description", "location", "date_reported", "contact_name", "contact_email")
        if any(not values[field] for field in required):
            flash("Please complete the required fields before publishing your report.", "error")
            return render_template("report.html", categories=get_categories(), form=values)

        item_id = create_item(**values)
        flash("Your report is live. We’ll help the right person find it.", "success")
        return redirect(url_for("item_detail", item_id=item_id))

    return render_template("report.html", categories=get_categories(), form={})


@app.route("/items/<int:item_id>")
def item_detail(item_id):
    item = get_item(item_id)
    if not item:
        flash("That listing is no longer available.", "error")
        return redirect(url_for("browse"))
    related_items = list_items(category=item["category"], limit=4, exclude_id=item_id)
    return render_template("item_detail.html", item=item, related_items=related_items)


@app.route("/items/<int:item_id>/claim", methods=["POST"])
def claim_item(item_id):
    item = get_item(item_id)
    if not item:
        flash("That listing is no longer available.", "error")
        return redirect(url_for("browse"))

    claimant_name = form_value("claimant_name")
    claimant_email = form_value("claimant_email")
    message = form_value("message")
    if not all([claimant_name, claimant_email, message]):
        flash("Add your name, email, and a short note so we can verify the match.", "error")
        return redirect(url_for("item_detail", item_id=item_id) + "#claim")

    add_claim(item_id, claimant_name, claimant_email, message)
    flash("Claim request sent. The reporter will receive your details shortly.", "success")
    return redirect(url_for("item_detail", item_id=item_id))


if __name__ == "__main__":
    import os
    initialize_portal()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)