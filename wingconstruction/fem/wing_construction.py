__author__ = "Juri Bieler"
__version__ = "0.0.1"
__status__ = "Development"

# ==============================================================================
# description     :interface to Calculix and solver-input-file generation
# author          :Juri Bieler
# date            :2018-07-13
# notes           :
# python_version  :3.6
# ==============================================================================

from wingconstruction.wingutils.constants import Constants


class WingConstruction:

    def __init__(self, project_path, half_span, box_depth, box_height, ribs, shell_thickness, engine_pos, box_overhang=0., stringer_height=0.):
        self.projectPath = project_path
        self.halfSpan = half_span
        self.boxDepth = box_depth
        self.boxHeight = box_height
        self.ribs = ribs
        self.shellThickness = shell_thickness
        self.enginePos = engine_pos
        self.pylonHeight = 0.3
        self.boxOverhang = box_overhang
        self.elementSize = 0.1
        self.stringerHeight = stringer_height
        self.beamLoad = False

    def calc_weight(self, density):
        """
        :param density: density of the material (SI)
        :return: the weight of the boy-structure in kg
        """
        v_box = self.halfSpan * 2. * (self.boxHeight + self.boxDepth) * self.shellThickness
        v_ribs = self.ribs * self.boxHeight * self.boxDepth * self.shellThickness
        w = (v_box + v_ribs) * density
        return w

    @staticmethod
    def calc_weight_stat(half_span, box_depth, box_height, ribs, shell_thickness, density):
        """

        :param half_span: half span in m
        :param box_depth: box depth in m
        :param box_height: box height in m
        :param ribs: rib count
        :param shell_thickness: shell thickness in m
        :param density: density of the material (SI)
        :return: the weight of the boy-structure in kg
        """
        v_box = half_span * 2. * (box_height + box_depth) * shell_thickness
        v_ribs = ribs * box_height * box_depth * shell_thickness
        w = (v_box + v_ribs) * density
        return w

    def calc_span_division(self, length):
        return self.calc_division(length)

    # the division shouldn't be odd or 0
    def calc_division(self, length):
        div = int(length / self.elementSize)
        if div == 0:
            div = 2
        if div % 2 > 0:
            div += 1
        return div

    def generate_wing(self, force_top, force_bot, engine_weight, element_size, element_type='qu4'):
        """
        generates a input file for calculix defining the wing structure
        :param force_top: the force evenly distributed on the top of the wing-box surface
        :param force_bot: the force evenly distributed on the bottom of the wing-box surface
        :param engine_weight: weight of the engine
        :param element_size: size of one element
        :param element_type: type name string of the elements (e.g. qu4, qu8)
        :return: None
        """
        self.elementSize = element_size
        out_lines = []
        out_lines.append('# draw flat T as lines')
        out_lines.append('# top right corner')
        out_lines.append('pnt pc 0 0 0')
        out_lines.append('seta pc all')
        out_lines.append('swep pc new tra 0 0 {:f} {:d}'.format(self.boxHeight, self.calc_division(self.boxHeight)))
        out_lines.append('swep pc new tra 0 {:f} 0 {:d}'.format(self.boxDepth, self.calc_division((self.boxDepth))))
        if self.boxOverhang > 0.:
            out_lines.append('swep pc new tra 0 {:f} 0 {:d}'.format(-1*self.boxOverhang, self.calc_division(self.boxOverhang)))
        out_lines.append('')
        out_lines.append('# top left corner')
        out_lines.append('pnt pc2 0 {:f} 0'.format(self.boxDepth))
        out_lines.append('seta pc2 pc2')
        out_lines.append('swep pc2 new tra 0 0 {:f} {:d}'.format(self.boxHeight, self.calc_division(self.boxHeight)))
        if self.boxOverhang > 0.:
            out_lines.append('swep pc2 new tra 0 {:f} 0 {:d}'.format(self.boxOverhang, self.calc_division(self.boxOverhang)))
        out_lines.append('')
        out_lines.append('# lower right corner')
        out_lines.append('pnt lowRightCorn 0 0 {:f}'.format(self.boxHeight))
        out_lines.append('seta lowRightCorn lowRightCorn')
        if self.boxOverhang > 0.:
            out_lines.append('swep lowRightCorn lowLeftCorn tra 0 {:f} 0 {:d}'.format(-1*self.boxOverhang, self.calc_division(self.boxOverhang)))
        out_lines.append('swep lowRightCorn lowLeftCorn tra 0 {:f} 0 {:d}'.format(self.boxDepth, self.calc_division(self.boxDepth)))
        out_lines.append('')
        if self.boxOverhang > 0.:
            out_lines.append('# lower left corner')
            out_lines.append('pnt pc4 0 {:f} {:f}'.format(self.boxDepth, self.boxHeight))
            out_lines.append('seta pc4 pc4')
            out_lines.append('swep pc4 new tra 0 {:f} 0 {:d}'.format(self.boxOverhang, self.calc_division(self.boxOverhang)))
            out_lines.append('')

        if self.stringerHeight > 0.:
            out_lines.append('# stringer')
            out_lines.append('pnt str0 0 0.3 0')
            out_lines.append('seta str0 str0')
            out_lines.append('swep str0 str0 tra 0 0 {:f} 2'.format(self.stringerHeight))
            out_lines.append('')
            out_lines.append('pnt str1 0 0.9 0')
            out_lines.append('seta str1 str1')
            out_lines.append('swep str1 str1 tra 0 0 {:f} 2'.format(self.stringerHeight))
            out_lines.append('')

            out_lines.append('pnt str2 0 0.3 0.55')
            out_lines.append('seta str2 str2')
            out_lines.append('swep str2 str2 tra 0 0 {:f} 2'.format(-1.*self.stringerHeight))
            out_lines.append('')
            out_lines.append('pnt str3 0 0.9 0.55')
            out_lines.append('seta str3 str3')
            out_lines.append('swep str3 str3 tra 0 0 {:f} 2'.format(-1*self.stringerHeight))
            out_lines.append('')

        out_lines.append('seta II2d all')
        out_lines.append('')

        out_lines.append('# extrude the II')
        spanDiv = self.calc_span_division(self.halfSpan)
        out_lines.append('swep II2d II2dOppo tra {:f} 0 0 {:d}'.format(self.halfSpan, spanDiv))
        out_lines.append('# make surfaces face outside')
        out_lines.append('seta toflip s A002 A005 A006')
        out_lines.append('flip toflip')
        out_lines.append('# new set for II beam')
        out_lines.append('seta II all')
        out_lines.append('')
        out_lines.append('# define top and bottom shell for load')
        out_lines.append('seta loadTop s A002')
        out_lines.append('comp loadTop d')
        if self.boxOverhang > 0.:
            out_lines.append('seta loadBot s A007')
        else:
            out_lines.append('seta loadBot s A004')
        out_lines.append('comp loadBot d')

        out_lines.append('#generate engine pylon')
        out_lines.append('seto pyl')
        out_lines.append('pnt pylP {:f} 0 {:f}'.format(self.enginePos, self.boxHeight))
        out_lines.append('swep pyl pyl tra 0 0 {:f} 6 a'.format(self.pylonHeight))
        out_lines.append('swep pyl pyl tra 0 {:f} 0 {:d} a'.format(self.boxDepth, self.calc_division(self.boxDepth)))
        out_lines.append('setc pyl')
        out_lines.append('')

        for i in range(0, self.ribs):
            if self.ribs <= 1:
                span_pos = 0
            else:
                span_pos = i * (self.halfSpan / (self.ribs - 1))
            pt_name = 'rp{:d}'.format(i)
            rib_name = 'rib{:d}'.format(i)
            out_lines.append('')
            out_lines.append('# generate a rib{:d}'.format(i))
            out_lines.append('seto ' + rib_name)
            out_lines.append('pnt '+pt_name+' {:f} 0 0'.format(span_pos))
            out_lines.append('swep '+rib_name+' '+rib_name+' tra 0 0 {:f} {:d} a'.format(self.boxHeight, self.calc_division((self.boxHeight))))
            out_lines.append('swep '+rib_name+' '+rib_name+' tra 0 {:f} 0 {:d} a'.format(self.boxDepth, self.calc_division(self.boxDepth)))
            out_lines.append('setc ' + rib_name)

        out_lines.append('')
        out_lines.append('# mesh it')
        out_lines.append('elty all '+element_type)
        out_lines.append('mesh all')
        out_lines.append('')

        out_lines.append('# merge beam nodes to get one big body')
        out_lines.append('seta nodes n II rib0')
        out_lines.append('merg n nodes')
        out_lines.append('')

        out_lines.append('# write surface files for TIEs')
        out_lines.append('send II abq sur')
        out_lines.append('')
        out_lines.append('seta pylL s pyl')
        #if self.stringerHeight > 0.:
        #    out_lines.append('seta pylL l L00Y')
        #else:
        #    out_lines.append('seta pylL l L00I')
        out_lines.append('comp pylL do')
        out_lines.append('comp pylL do')
        out_lines.append('send pylL abq sur')
        out_lines.append('')

        for i in range(1, self.ribs):
            # here we use 's' to make it abaqus compatible, l is working for calculix
            # s however causes warinings in caluclix
            out_lines.append('seta ribL{:d} s rib{:d}'.format(i, i))
            out_lines.append('comp ribL{:d} do'.format(i))
            out_lines.append('comp ribL{:d} do'.format(i))
            out_lines.append('send ribL{:d} abq sur'.format(i))
        out_lines.append('')

        out_lines.append('# write bc')
        out_lines.append('seta bc n rib0')
        out_lines.append('send bc abq nam')
        out_lines.append('enq bc bc2 rec 0 _ 0.275 0.1')
        out_lines.append('send bc2 abq nam')
        out_lines.append('')

        out_lines.append('# write msh file')
        out_lines.append('send all abq')
        out_lines.append('')

        if self.beamLoad:
            node_count = (self.calc_span_division(self.halfSpan) + 1) * 2
        else:
            node_count = (self.calc_span_division(self.halfSpan)+1) * (self.calc_division(self.boxDepth)+1)
            if element_type == 'qu8':
                node_count -= 0.5*self.calc_span_division(self.halfSpan) * 0.5*self.calc_division(self.boxDepth)
        node_count_engine = self.calc_division(self.boxDepth) + 1
        noad_load_top = force_top/node_count
        noad_load_bot = force_bot / node_count
        node_load_engine = engine_weight / node_count_engine
        if self.beamLoad:
            out_lines.append('# fix load node sets so only the beams are affected')
            out_lines.append('#top')
            out_lines.append('seta loadTopN n loadTop')
            out_lines.append('enq loadTopN loadTopLine1 rec _ 0. 0. 0.001')
            out_lines.append('enq loadTopN loadTopLine2 rec _ {:f} 0. 0.001'.format(self.boxDepth))
            out_lines.append('setr loadTop n all')
            out_lines.append('seta loadTop n loadTopLine1 loadTopLine2')
            out_lines.append('#top')
            out_lines.append('seta loadBotN n loadBot')
            out_lines.append('enq loadBotN loadBotLine1 rec _ 0. {:f} 0.001'.format(self.boxHeight))
            out_lines.append('enq loadBotN loadBotLine2 rec _ {:f} {:f} 0.001'.format(self.boxDepth, self.boxHeight))
            out_lines.append('setr loadBot n all')
            out_lines.append('seta loadBot n loadBotLine1 loadBotLine2')
        out_lines.append('# load application')
        out_lines.append('# top')
        out_lines.append('send loadTop abq force 0 0 {:f}'.format(noad_load_top))
        out_lines.append('# bottom')
        out_lines.append('send loadBot abq force 0 0 {:f}'.format(noad_load_bot))
        out_lines.append('#engine weight')
        out_lines.append('seta engNodes n pyl')
        out_lines.append('enq engNodes engLoad rec {:f} _ {:f} 0.01'.format(self.enginePos, self.boxHeight+self.pylonHeight))
        out_lines.append('send engLoad abq force 0 0 {:f}'.format(node_load_engine))
        out_lines.append('')
        out_lines.append('')

        out_lines.append('# plot it')
        out_lines.append('rot -y')
        out_lines.append('rot r 110')
        out_lines.append('rot u 20')
        out_lines.append('seta ! all')
        out_lines.append('frame')
        out_lines.append('zoom 2')
        out_lines.append('view elem')
        out_lines.append('plus n loadTop g')
        out_lines.append('plus n loadBot y')
        out_lines.append('plus n bc r')
        out_lines.append('plus n II2dOppo b')
        out_lines.append('hcpy png')
        out_lines.append('sys mv hcpy_1.png mesh.png')
        out_lines.append('')
        out_lines.append('quit')
        f = open(self.projectPath + '/wingGeo.fbl', 'w')
        f.writelines(line + '\n' for line in out_lines)
        f.close()

    def generate_inp(self, nonlinear=False):
        """
        generates input file that includes the prev. generated geometry files
        :param nonlinear: True if calculation should be non-linear
        :return: None
        """
        material_young = Constants().config.getfloat('defaults', 'material_young')
        material_poisson = Constants().config.getfloat('defaults', 'material_poisson')
        out_lines = []
        out_lines.append('** load mesh- and bc-file')
        out_lines.append('*include, input=all.msh')
        out_lines.append('*include, input=bc.nam')
        out_lines.append('*include, input=bc2.nam')
        out_lines.append('*include, input=II.sur')
        out_lines.append('*include, input=pylL.sur')
        for i in range(1, self.ribs):
            out_lines.append('*include, input=ribL{:d}.sur'.format(i))
        out_lines.append('')
        out_lines.append('** constraints')
        out_lines.append('*boundary')
        out_lines.append('Nbc,1')
        out_lines.append('Nbc2,1,6')
        out_lines.append('')
        out_lines.append('** material definition')
        out_lines.append('*Material, name=ALU')
        out_lines.append('*Elastic')
        out_lines.append(' {:.3e}, {:.3f}'.format(material_young, material_poisson))
        out_lines.append('** workaround (if after material prop is a empty row it dows not work)')
        #out_lines.append('')
        out_lines.append('** define surfaces')
        out_lines.append('*shell section, elset=Eall, material=ALU')
        out_lines.append('{:f}'.format(self.shellThickness))
        out_lines.append('')
        out_lines.append('*tie,name=tpyl,position tolerance=0.01')
        out_lines.append('SpylL,SII')
        out_lines.append('')
        for i in range(1, self.ribs):
            out_lines.append('*tie,name=trib{:d},position tolerance=0.01'.format(i))
            out_lines.append('SribL{:d},SII'.format(i))
            out_lines.append('')
        out_lines.append('** step')
        if nonlinear:
            out_lines.append('*step, nlgeom')
        else:
            out_lines.append('*step')
        out_lines.append('*static')
        out_lines.append('')
        out_lines.append('** load')
        out_lines.append('*cload')
        out_lines.append('*include, input=loadTop.frc')
        out_lines.append('*include, input=loadBot.frc')
        out_lines.append('*include, input=engLoad.frc')
        out_lines.append('')
        out_lines.append('*node file')
        out_lines.append('U')
        out_lines.append('*el file')
        out_lines.append('S')
        out_lines.append('*end step')
        out_lines.append('')
        f = open(self.projectPath + '/wingRun.inp', 'w')
        f.writelines(line + '\n' for line in out_lines)
        f.close()


if __name__ == '__main__':
    geo = WingConstruction()
    geo.generate_wing('../data_out/test01/test', 5, 0.1, 0.1, 0.1)
    geo.generate_inp('../data_out/test01/test', 2.)