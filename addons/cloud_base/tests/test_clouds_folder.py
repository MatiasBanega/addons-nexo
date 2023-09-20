# -*- coding: utf-8 -*-

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class TestCloudsFolder(TransactionCase):
    """
    Test data for clouds folder required for clouds folder creation
    """
    def setUp(self):
        """
        Set up test data
        The app depends only on 'mail', so in tests we may rely upon the models which definitely exist based on 
        dependencies: 'res.partner', 'res.country', etc
        """
        super(TestCloudsFolder, self).setUp()
        # partner data which is going to be used for folders structure
        self.parent_company1 = self.env["res.partner"].create({"name": "[TEST-CLOUD] COMPANY 1"})
        self.contact1 = self.env["res.partner"].create({
            "name": ".[TEST-CLOUD] \\//#~ CONTACT 1", 
            "parent_id": self.parent_company1.id,
            "phone": "123456789",
        })
        self.contact2 = self.env["res.partner"].create({
            "name": ".[TEST-CLOUD] ----- CONTACT 1.1", 
            "parent_id": self.parent_company1.id,
            "phone": "123456789",
        })
        self.parent_company2 = self.env["res.partner"].create({"name": "[TEST-CLOUD] COMPANY 2"})
        self.contact3 = self.env["res.partner"].create({
            "name": "[TEST-CLOUD] CONTACT 2", 
            "parent_id": self.parent_company2.id
        })
        # Folder rules (sync model)
        res_partner_model = self.env["ir.model"].search([("model", "=", "res.partner")], limit=1)
        self.sync_model1 = self.env["sync.model"].create({
            "name": "[TEST-CLOUD] Parent companies",
            "model_id": res_partner_model.id,
            "domain": '[("parent_id", "=", False), ("name", "ilike", "[TEST-CLOUD]")]',
            "sequence": 1,
        })
        self.sync_model2 = self.env["sync.model"].create({
            "name": "[TEST-CLOUD] CHILD CONTACTS",
            "model_id": res_partner_model.id,
            "parent_id": self.sync_model1.id,
            "parent_field": "parent_id",
            "domain": '[("name", "ilike", "[TEST-CLOUD]")]',
            "name_expression": "${object.name}${object.phone and ' '+object.phone or ''}.",
            "sequence": 2,
        })
        # cloud client sample data
        cloud_client_options = self.env["clouds.client"]._fields["cloud_client"].get_values(self.env)
        self.cloud_client_1 = self.env["clouds.client"].create({
            "name": ". [TEST-CLOUD] cloud client 1 \\//#~.",
            # for testing purposes we may assume that client is confirmed without workflow
            "state": "confirmed",
            # if only cloud_base installed, the field is not required. Otherwise, we can use any value
            "cloud_client": cloud_client_options and cloud_client_options[0] or False,
            "root_folder_name": ". [TEST-CLOUD] cloud client 1 \\//#~.",
        })
        self.cloud_client_2 = self.env["clouds.client"].create({
            "name": "[TEST-CLOUD] cloud client 2",
            "state": "confirmed",
            "cloud_client": cloud_client_options and cloud_client_options[0] or False,
            "root_folder_name": "[TEST-CLOUD] cloud client 2",
        })
        # manual folders
        self.folder_0 = self.env["clouds.folder"].create({
            "name": "[TEST-CLOUD] manual 0",
            "own_client_id": self.cloud_client_2.id,
        })
        self.folder_0_1 = self.env["clouds.folder"].create({
            "name": "[TEST-CLOUD] manual 0.1",
            "parent_id": self.folder_0.id,
        })
        self.folder_0_1_1 = self.env["clouds.folder"].create({
            "name": "[TEST-CLOUD] manual 0.1.1",
            "parent_id": self.folder_0_1.id,
            "own_client_id": self.cloud_client_1.id,
        })
        self.folder_1 = self.env["clouds.folder"].create({
            "name": "[TEST-CLOUD] manual 1",
        })

    def _cron_trigger_check(self):
        """
        The method to launch cron to update folders
        """
        cron_id = self.env.ref("cloud_base.cloud_base_prepare_folders")
        cron_id.with_context(cloud_testing=True).method_direct_trigger()

@tagged('-at_install', 'post_install')
class TestCloudsFolderPreparing(TestCloudsFolder):
    """
    Testing suite for cloud clients, sync rules, and folders changes and updates
    """
    def test1_general_cron_triggering(self):
        """
        Test folders structure and its changes based on sample data, rules, and triggered cron jobs

        Desired folders structure:
        -- Parent companies
            -- [TEST-CLOUD] COMPANY 1
                -- CHILD CONTACTS
                    -- [TEST-CLOUD] CONTACT 1
                    -- [TEST-CLOUD] CONTACT 1 (/ID of created contact/)
            -- [TEST-CLOUD] COMPANY 2 ---
                -- CHILD CONTACTS
                    -- [TEST-CLOUD] CONTACT 2
        """
        self._cron_trigger_check()       
        rule_folder_1 = self.env["clouds.folder"].search([
            ("rule_id", "=", self.sync_model1.id),
            ("name", "=", "[TEST-CLOUD] Parent companies"),
        ])
        rule_folder_1_1 = self.env["clouds.folder"].search([
            ("rule_id", "=", self.sync_model1.id),
            ("name", "=", "[TEST-CLOUD] COMPANY 1"),
            ("parent_id", "=", rule_folder_1.id),
        ])
        rule_folder_1_1_1 = self.env["clouds.folder"].search([
            ("rule_id", "=", self.sync_model2.id),
            ("name", "=", "[TEST-CLOUD] CHILD CONTACTS"),
            ("parent_id", "=", rule_folder_1_1.id),
        ])
        rule_folder_1_1_1_1 = self.env["clouds.folder"].search([
            ("rule_id", "=", self.sync_model2.id),
            ("name", "=", "[TEST-CLOUD] ----- CONTACT 1 123456789"),
            ("parent_id", "=", rule_folder_1_1_1.id),
        ])
        rule_folder_1_1_1_2 = self.env["clouds.folder"].search([
            ("rule_id", "=", self.sync_model2.id),
            ("name", "=", "[TEST-CLOUD] ----- CONTACT 1.1 123456789"),
            ("parent_id", "=", rule_folder_1_1_1.id),
        ])
        rule_folder_1_2 = self.env["clouds.folder"].search([
            ("rule_id", "=", self.sync_model1.id),
            ("name", "=", "[TEST-CLOUD] COMPANY 2"),
            ("parent_id", "=", rule_folder_1.id),
        ])
        rule_folder_1_2_1 = self.env["clouds.folder"].search([
            ("rule_id", "=", self.sync_model2.id),
            ("name", "=", "[TEST-CLOUD] CHILD CONTACTS"),
            ("parent_id", "=", rule_folder_1_2.id),
        ])
        rule_folder_1_2_1_1 = self.env["clouds.folder"].search([
            ("rule_id", "=", self.sync_model2.id),
            ("name", "=", "[TEST-CLOUD] CONTACT 2"),
            ("parent_id", "=", rule_folder_1_2_1.id),
        ])

        # Case 1
        # Tested '[TEST-CLOUD] Parent companies': model-related folder creation
        self.assertEqual(len(rule_folder_1), 1)
        # Case 2
        # Tested '[TEST-CLOUD] COMPANY 1': object-related folder creation
        self.assertEqual(len(rule_folder_1_1), 1)
        # Case 3
        # Tested '[TEST-CLOUD] CHILD CONTACTS': model-related folder as a subfolder for an object-related
        self.assertEqual(len(rule_folder_1_1_1), 1)
        # Case 4 
        # Tested '[TEST-CLOUD] CONTACT 1': object-related folder creation under model-related subfolder
        # Tested name expression rendering
        # Tested illegal symbols replacement
        self.assertEqual(len(rule_folder_1_1_1_1), 1)
        # Case 5
        # Tested '[TEST-CLOUD] CONTACT 1 /ID/': object-related folder creation under model-related subfolder      
        # Tested renaming of a linked model (based on name expression)
        # Tested the same name within a root folder (should add an id of a linked model)
        self.contact2.write({"name": "[TEST-CLOUD] ----- CONTACT 1"})
        self._cron_trigger_check()
        rule_folder_1_1_1_2a = self.env["clouds.folder"].search([
            ("rule_id", "=", self.sync_model2.id),
            ("name", "=", "[TEST-CLOUD] ----- CONTACT 1 123456789 ({})".format(rule_folder_1_1_1_2.id)),
            ("parent_id", "=", rule_folder_1_1_1.id),
        ])
        self.assertEqual(len(rule_folder_1_1_1_2a), 1)

        # Case 6
        # Tested deactivating of sync rule:
        #   * Everything within 'CHILD contacts' should be deactivated
        #   * Child rules should be deactivated
        # Testing activating it back 
        #   * each folder should be recovered, no new folders are created
        #   * child rules should remain deactivated
        self.sync_model1.write({"active": False})
        self.assertFalse(self.sync_model2.active)
        self._cron_trigger_check()
        self.assertEqual(len(rule_folder_1_1.child_ids), 0)
        self.assertFalse(rule_folder_1_1_1_1.active)
        self.sync_model1.write({"active": True})
        self.assertFalse(self.sync_model2.active)
        self.sync_model2.write({"active": True})
        self._cron_trigger_check()
        self.assertEqual(len(rule_folder_1_1.child_ids), 1)
        self.assertEqual(len(rule_folder_1_1_1.child_ids), 2)

        # Case 7
        # Tested object re-assigning to a new object-related folder (contact changes its parent company). 
        # Folder [TEST-CLOUD] CONTACT 2 should be moved to [TEST-CLOUD] COMPANY 1 > CHILD CONTACTS
        self.contact3.write({"parent_id": self.parent_company1.id})
        self._cron_trigger_check()
        self.assertEqual(rule_folder_1_2_1_1.parent_id.id, rule_folder_1_1_1.id)
        self.contact3.write({"parent_id": self.parent_company2.id})
        self._cron_trigger_check()

        # Case 8
        # Tested the same object ("Company 1") relates for 2 rules
        #   * If this new rule has higher sequence > the previous folder should be kept 
        #   * Otherwise it should be moved. Child subsolfers (based on child rules) should be deactivated 
        # In both scenarios NO 2 object-related folder should be created 
        self.sync_model3 = self.env["sync.model"].create({
            "name": "COMPANY 1", 
            "model_id": self.sync_model1.model_id.id,
            "domain": '[("name", "ilike", "[TEST-CLOUD]"), ("name", "ilike", "COMPANY 1"), ("parent_id", "=", False),]',
            "name_expression": "${object.name}${object.phone and ' '+object.phone or ''}.",
            "sequence": 3,
        })
        self._cron_trigger_check()
        rule_folder_2 = self.env["clouds.folder"].search([
            ("name", "=", "COMPANY 1"),
            ("rule_id", "=", self.sync_model3.id),
        ])
        rule_folder_2_1 = self.env["clouds.folder"].search([("name", "=", "[TEST-CLOUD] COMPANY 1")])
        self.assertEqual(rule_folder_2_1.id, rule_folder_1_1.id)
        self.assertEqual(len(rule_folder_2_1), 1)
        self.assertEqual(rule_folder_2_1.parent_id.id, rule_folder_1.id)  
        self.sync_model3.write({"sequence": 0})
        self._cron_trigger_check()
        rule_folder_2_1 = self.env["clouds.folder"].search([("name", "=", "[TEST-CLOUD] COMPANY 1"),])
        self.assertEqual(rule_folder_2_1.id, rule_folder_1_1.id)
        self.assertEqual(len(rule_folder_2_1), 1)
        self.assertEqual(rule_folder_2_1.parent_id.id, rule_folder_2.id)  
        self.sync_model3.write({"sequence": 3})
        self._cron_trigger_check()

    def test2_cloud_clients_computing(self):
        """
        Test cloud client data
        """
        # Case 1
        # Tested removing illegal characters in root folder names
        self.assertEqual(self.cloud_client_1.root_folder_name, "[TEST-CLOUD] cloud client 1 -----")

        # Case 2
        # Tested that sync model inherit clients correctly: child rule should have the same client_id
        self.sync_model1.write({"own_client_id": self.cloud_client_1.id})
        self.sync_model2.write({"own_client_id": self.cloud_client_2.id})
        self.assertEqual(self.sync_model1.client_id, self.sync_model2.client_id)

        # Case 3
        # Tested that cloud folders inherit rule related clients
        self._cron_trigger_check()
        rule_folder_1 = self.env["clouds.folder"].search([
            ("rule_id", "=", self.sync_model1.id),
            ("name", "=", "[TEST-CLOUD] Parent companies"),
        ], limit=1)
        rule_folder_1_1_1_2 = self.env["clouds.folder"].search([
            ("rule_id", "=", self.sync_model2.id),
            ("name", "=", "[TEST-CLOUD] ----- CONTACT 1.1 123456789"),
        ], limit=1)
        self.assertEqual(rule_folder_1.client_id, self.cloud_client_1)
        self.assertEqual(rule_folder_1_1_1_2.client_id, self.cloud_client_1)

        # Case 4
        # Tested manually created folders under different hierarchy and rule-relations

        self.assertEqual(self.folder_0_1_1.client_id, self.cloud_client_2)

        self.folder_0_1_1.write({"parent_id": False})
        self.assertEqual(self.folder_0_1_1.client_id, self.cloud_client_1)

        self.folder_1.write({"parent_id": self.folder_0.id})
        self.folder_0.write({"parent_id": rule_folder_1_1_1_2.id})
        self.assertEqual(self.folder_1.client_id, self.cloud_client_1)

        self.folder_0_1.write({"parent_id": False})
        self.assertEqual(self.folder_0_1.client_id.id, False)

        # Case 5
        # Tested cloud client resetting
        self.cloud_client_1._reset_connection()
        self.assertEqual(self.sync_model1.client_id.id, False)
        self.assertEqual(self.sync_model2.client_id.id, False)
        self.assertEqual(rule_folder_1.client_id.id, False)
        self.assertEqual(rule_folder_1_1_1_2.client_id.id, False)
        self.assertEqual(self.folder_0.client_id.id, False)
        self.assertEqual(self.folder_1.client_id.id, False)

    def test3_security_rights_check(self):
        """
        Test applied security
        """
        self._cron_trigger_check()
        rule_folder_1 = self.env["clouds.folder"].search([
            ("rule_id", "=", self.sync_model1.id),
            ("name", "=", "[TEST-CLOUD] Parent companies"),
        ], limit=1)
        rule_folder_1_1_1_2 = self.env["clouds.folder"].search([
            ("rule_id", "=", self.sync_model2.id),
            ("name", "=", "[TEST-CLOUD] ----- CONTACT 1.1 123456789"),
        ], limit=1)
        self.folder_0.write({"parent_id": rule_folder_1_1_1_2.id})
        
        cloud_user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': '[TEST-CLOUD] default_user_salesman_2',
            'login': 'default_user_salesman_2',
            'email': 'default_user_salesman_2@example.com',
            'signature': '--\nMark',
            'notification_type': 'email',
            'groups_id': [(6, 0, (self.env.ref('base.group_user') + self.env.ref('base.group_partner_manager')).ids)],
        })

        # Case 1
        # Tested that rule-related folders cannot be updated manually
        with self.assertRaises(AccessError):
            rule_folder_1.with_user(cloud_user.id).write({})

        # simulate security block
        partner_model = self.env["ir.model"].search([("model", "=", "res.partner")], limit=1)
        security_hack = self.env["ir.rule"].create({
            "name": "[TEST-CLOUD] partner simulated full restriction",
            "model_id": partner_model.id,
            "domain_force": [("name", "=", "BAD")],
        })

        # Case 2 
        # Tested access to rule-related folder, when its related object is blocked for the user
        with self.assertRaises(AccessError):
            rule_folder_1_1_1_2.with_user(cloud_user.id).read(["name"])
        with self.assertRaises(AccessError):
            self.folder_0.with_user(cloud_user.id).read(["name"])            

        # Case 3
        # Tested attachment related for manual cloud folder
        attachment_id = self.env["ir.attachment"].create({
            "name": "[TEST-CLOUD] Sample attachment",
            "clouds_folder_id": self.folder_0.id,
        })
        with self.assertRaises(AccessError):
            attachment_id.with_user(cloud_user.id).read(["name"])

        # CASE 4 
        # Tested that even if possible to read, it would not be possible to write if restricted
        security_hack.write({
            "perm_read": False,
            "perm_write": True,
            "perm_create": True,
            "perm_unlink": True,
        })
        self.folder_0.with_user(cloud_user.id).read(["name"])
        with self.assertRaises(AccessError):
            self.folder_0.with_user(cloud_user.id).write({})         
        with self.assertRaises(AccessError):
            self.env["clouds.folder"].with_user(cloud_user.id).create({
                "name": "[TEST-CLOUD] Subfolder creation",
                "parent_id": self.folder_0.id,
            }) 

        # Case 5
        # Tested that own folder restriction take place
        security_hack.unlink()
        self.folder_0.write({"access_user_ids": [(6, 0, self.env.ref('base.user_root').ids)]})

        with self.assertRaises(AccessError):
            self.folder_0.with_user(cloud_user.id).read({})        
        with self.assertRaises(AccessError):
            self.folder_0_1_1.with_user(cloud_user.id).read({})


    def test4_attachments_folder_rel_check(self):
        """
        Test changes in attachments <> clouds
        """
        self._cron_trigger_check()
        rule_folder_1 = self.env["clouds.folder"].search([
            ("rule_id", "=", self.sync_model1.id),
            ("name", "=", "[TEST-CLOUD] Parent companies"),
        ], limit=1)
        rule_folder_1_1_1_2 = self.env["clouds.folder"].search([
            ("rule_id", "=", self.sync_model2.id),
            ("name", "=", "[TEST-CLOUD] ----- CONTACT 1.1 123456789"),
        ], limit=1)
        self.folder_0.write({"parent_id": rule_folder_1_1_1_2.id})

        # Case 1 
        # Tested manual-folder related attachment has its res_id and 'clouds.folder' as res model
        attachment_id = self.env["ir.attachment"].create({
            "name": "[TEST-CLOUD] Sample attachment",
            "clouds_folder_id": self.folder_0.id,
        })
        self.assertEqual(attachment_id.res_id, self.folder_0.id)

        # Case 2
        # Tested that rule-related folder has rule model and empty res_id
        self.assertEqual(rule_folder_1.res_model, "res.partner")
        self.assertEqual(rule_folder_1.res_id, 0)
        
        # Case 3
        # Tested that this folder attachments have this folder_id as res_id and clouds.folder as res_model
        attachment_id = self.env["ir.attachment"].create({
            "name": "[TEST-CLOUD] Sample attachment",
            "clouds_folder_id": rule_folder_1.id,
        })
        self.assertEqual(attachment_id.res_model, "clouds.folder")
        self.assertEqual(attachment_id.res_id, rule_folder_1.id)        

        # Case 4
        # Tested that object-related folder and its attachments have res_model and res_id of that object
        self.assertEqual(rule_folder_1_1_1_2.res_model, "res.partner")
        self.assertEqual(rule_folder_1_1_1_2.res_id, self.contact2.id)
        attachment_id = self.env["ir.attachment"].create({
            "name": "[TEST-CLOUD] Sample attachment",
            "clouds_folder_id": rule_folder_1_1_1_2.id,
        })
        self.assertEqual(attachment_id.res_model,  "res.partner")
        self.assertEqual(attachment_id.res_id, self.contact2.id)        
