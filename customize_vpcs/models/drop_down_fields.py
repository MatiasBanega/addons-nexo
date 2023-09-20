from odoo import models, fields, api, _


class BargeRoad(models.Model):
    _name = "barge.road"

    name = fields.Char("Name")


class BargeFrom(models.Model):
    _name = "barge.from"

    name = fields.Char("Name")


class BargeTo(models.Model):
    _name = "barge.to"

    name = fields.Char("Name")


class TugModel(models.Model):
    _name = "tug.model"

    name = fields.Char("Name")


# class BargeOperator(models.Model):
#     _name = "barge.operator"
#
#     name = fields.Char("Name")


class LastLocation(models.Model):
    _name = "last.known.location"

    name = fields.Char("Name")


class TransporterName(models.Model):
    _name = "transporter.name"

    name = fields.Char("Name")


class CurrentEmptyLocation(models.Model):
    _name = "current.empty.location"

    name = fields.Char("Name")

