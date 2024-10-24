from odoo.exceptions import ValidationError
from odoo import models, fields, api
from string import ascii_letters, digits, whitespace

from lxml import etree
from lxml.builder import E
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG

def name_boolean_group(id):
    return 'in_group_' + str(id)

def name_selection_groups(ids):
    return 'sel_groups_' + '_'.join(str(it) for it in sorted(ids))

def is_boolean_group(name):
    return name.startswith('in_group_')

def is_selection_groups(name):
    return name.startswith('sel_groups_')

def is_reified_group(name):
    return is_boolean_group(name) or is_selection_groups(name)

def get_boolean_group(name):
    return int(name[9:])

def get_selection_groups(name):
    return [int(v) for v in name[11:].split('_')]

class Grupos(models.Model):    
    _inherit = 'res.groups'
    
    
     
    def activar_perfiles_activo(self):        
        self.action_activo()
        view = self.env.ref('wizard-message.sh_message_wizard')
        view_id = view and view.id or False
        context = dict(self._context or{})
        context['message']= "Proceso finalizado con exito!!!!!"
        return{
            'name':'Mensaje',
            'type':'ir.actions.act_window',
            'view_type': 'form',
            'res_model':'sh.message.wizard',
            'views': [(view.id, 'form')],
            'view_id':view.id,
            'target':'new',
            'context':context,
        }

    def action_activo(self):
        # raise ValidationError("lego")
        """ Modify the view with xmlid ``base.user_groups_view``, which inherits
            the user form view, and introduces the reified group fields.
        """
        # remove the language to avoid translations, it will be handled at the view level
        self = self.with_context(lang=None)

        # We have to try-catch this, because at first init the view does not
        # exist but we are already creating some basic groups.        
        view = self.env.ref('prefectura_equipos.user_groups_view_asset_inherit', raise_if_not_found=False)
        if not (view and view.exists() and view._name == 'ir.ui.view'):
            return

        if self._context.get('install_filename') or self._context.get(MODULE_UNINSTALL_FLAG):
            # use a dummy view during install/upgrade/uninstall
            xml = E.field(name="groups_id", position="after")

        else:
            group_no_one = view.env.ref('base.group_no_one')
            
            group_employee = view.env.ref('base.group_user')
            xml1, xml2, xml3 = [], [], []
            xml_by_category = {}
            # xml1.append(E.separator(string='User Type', colspan="2", groups='base.group_no_one'))

            user_type_field_name = ''
            user_type_readonly = str({})
            sorted_tuples = sorted(self.get_groups_by_application(),
                                   key=lambda t: t[0].xml_id != 'base.module_category_user_type')
            # raise ValidationError("tupla {}".format(sorted_tuples))
            _variable =[]
            for app, kind, gs, category_name in sorted_tuples:  # we process the user type first
                attrs = {}
                # hide groups in categories 'Hidden' and 'Extra' (except for group_no_one)
                if app.xml_id in self._get_hidden_extra_categories():
                    attrs['groups'] = 'base.group_no_one'
                if kind == 'selection' and app in [self.env.ref("prefectura_equipos.prefectura_categoria_equipos")]:
                    # application name with a selection field                    
                        field_name = name_selection_groups(gs.ids)
                        _variable.append(field_name)                        
                        attrs['attrs'] = user_type_readonly
                        if category_name not in xml_by_category:
                            xml_by_category[category_name] = []
                            xml_by_category[category_name].append(E.newline())
                        xml_by_category[category_name].append(E.field(name=field_name, **attrs))
                        xml_by_category[category_name].append(E.newline())
                    
                
                elif kind != 'selection' and app in [self.env.ref("prefectura_equipos.prefectura_categoria_adicional_equipos")]:
                    # application separator with boolean fields
                    app_name = app.name or 'Other'
                    xml3.append(E.separator(string=app_name, colspan="4", **attrs))
                    attrs['attrs'] = user_type_readonly
                    for g in gs:
                        field_name = name_boolean_group(g.id)
                        if g == group_no_one:
                            # make the group_no_one invisible in the form view
                            xml3.append(E.field(name=field_name, invisible="1", **attrs))
                        else:
                            xml3.append(E.field(name=field_name, **attrs))
          
            xml3.append({'class': "o_label_nowrap"})
            if user_type_field_name:
                user_type_attrs = {'invisible': [(user_type_field_name, '!=', group_employee.id)]}
            else:
                user_type_attrs = {}

            for xml_cat in sorted(xml_by_category.keys(), key=lambda it: it[0]):
                master_category_name = xml_cat[1]
                xml2.append(E.group(*(xml_by_category[xml_cat]), col="2", string=master_category_name))
                

            xml = E.field(
                E.group(*(xml1), col="2"),
                E.group(*(xml2), col="2", attrs=str(user_type_attrs)),
                E.group(*(xml3), col="4", attrs=str(user_type_attrs)), name="groups_id", position="replace")
            xml.addprevious(etree.Comment("GENERATED AUTOMATICALLY BY GROUPS"))
            

        # serialize and update the view
        xml_content = etree.tostring(xml, pretty_print=True, encoding="unicode")
        # raise ValidationError("llego {}".format(xml_content))
        if xml_content != view.arch:  # avoid useless xml validation if no change
            new_context = dict(view._context)
            new_context.pop('install_filename', None)  # don't set arch_fs for this computed view
            new_context['lang'] = None
            view.with_context(new_context).write({'arch': xml_content})
    
    
    
    
    

class Usuario(models.Model):    
    _inherit = 'res.users'
    
    @api.depends('groups_id')
    def _compute_share(self):
        
        user_group_id = self.env['ir.model.data']._xmlid_to_res_id('base.group_user')       
        internal_users = self.filtered_domain([('groups_id', 'in', [user_group_id])])
        internal_users.share = False
        (self - internal_users).share = True
        
    
    
                