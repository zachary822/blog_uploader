import argparse
from pathlib import Path

from pandocfilters import walk
from pymongo import MongoClient

from blog_uploader import markdown_to_ast, markdown_to_doc
from blog_uploader.create_post import create_post
from blog_uploader.image_uploaders.gridfs_uploader import GridFsUploader
from blog_uploader.schemas import Action
from blog_uploader.settings import settings

parser = argparse.ArgumentParser(prog="blog_uploader")

subparsers = parser.add_subparsers(title="actions", dest="action")
create_parser = subparsers.add_parser(Action.create)
create_parser.add_argument("title")

upload_parser = subparsers.add_parser(Action.upload)
upload_parser.add_argument("-p", "--publish", action="store_true")

publish_parser = subparsers.add_parser(Action.publish)
publish_parser.add_argument("-u", "--unpublish", action="store_true")

delete_parser = subparsers.add_parser(Action.delete)

parser.add_argument("file")
args = parser.parse_args()

if args.action == Action.create:
    with open(args.file, "x") as f:
        f.write(create_post(args.title))
else:
    with MongoClient(settings.mongodb_uri) as client, GridFsUploader(
        client.blog
    ) as image_client:
        db = client.blog

        if args.action == Action.upload:
            post = markdown_to_doc(args.file, image_uploader=image_client)
            post.published = args.publish
            db.posts.replace_one(
                {"_id": post.id},
                post.dict(by_alias=True),
                upsert=True,
            )
        elif args.action == Action.publish:
            post = markdown_to_doc(args.file)
            db.posts.update_one(
                {"_id": post.id}, {"$set": {"published": not args.unpublish}}
            )
        elif args.action == Action.delete:
            post = markdown_to_doc(args.file)
            mpath = Path(args.file)
            doc = markdown_to_ast(args.file)

            def _delete_image(key, value, format, meta):
                if key == "Image":
                    image_client.remove(mpath.parent / value[2][0])

            doc = walk(doc, _delete_image, "", doc["meta"])

            db.posts.delete_one({"_id": post.id})
