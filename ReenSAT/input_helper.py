import six
from crytic_compile import CryticCompile

from source_map import SourceMap


class InputHelper:

    def __init__(self, **kwargs):
        attr_defaults = {
            'source': None
        }
        for (attr, default) in six.iteritems(attr_defaults):
            val = kwargs.get(attr, default)
            if val == None:
                raise Exception("'%s' attribute can't be None" % attr)
            else:
                setattr(self, attr, val)

    def get_inputs(self):
        inputs = []
        com = CryticCompile(self.source)
        contracts = self._get_contracts_name(com)
        for contract in contracts:
            # '/root/helong/contracts/simpleDao.sol:SimpleDAO'
            c_source, cname = contract.split(':')
            source_map =SourceMap(contract, self.source)

            inputs.append({
                'contract': contract, # 文件名：合约名
                'source_map': source_map, # 源文件映射关系
                'source': self.source, # 文件名
                'c_source': c_source, # 文件名
                'c_name': cname, # 合约名
            })

        return inputs

    def _get_contracts_name(self, com: CryticCompile):
        return [(com.contracts_filenames[name].absolute + ':' + name) for name in com.contracts_names]

