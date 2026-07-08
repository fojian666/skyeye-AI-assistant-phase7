from .base_options import BaseOptions


class TestOptions(BaseOptions):
    """This class includes test options.
    """

    def initialize(self, parser):
        #parser = BaseOptions.initialize(self, parser)  # define shared options
        data = BaseOptions.init_data(self)
        data['ntest'] = float("inf")
        data['results_dir'] = ''
        data['aspect_ratio'] = 1.0
        data['phase'] = 'test'
        data['eval'] = ''
        data['num_test']=50
        # parser.add_argument('--ntest', type=int, default=float("inf"), help='# of test examples.')
        # parser.add_argument('--results_dir', type=str, default=r'F:\杨光迪变化检测论文数据\111\result', help='saves results here.')
        # parser.add_argument('--aspect_ratio', type=float, default=1.0, help='aspect ratio of result images')
        # parser.add_argument('--phase', type=str, default='test', help='train, val, test, etc')
        # # Dropout and Batchnorm has different behavioir during training and test.
        # parser.add_argument('--eval', action='store_true', help='use eval mode during test time.')
        # parser.add_argument('--num_test', type=int, default=50, help='how many test images to run')
        # # To avoid cropping, the load_size should be the same as crop_size
        # parser.set_defaults(load_size=parser.get_default('crop_size'))
        self.isTrain = False
        #return parser
        return data
