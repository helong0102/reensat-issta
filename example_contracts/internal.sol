pragma solidity ^0.4.19;

contract Test_transfer_or_sender{
	function _withdraw(address to, address token, uint256 amount) internal {
		if (token == address(0)) {
			to.call.value(amount);
		}
	}
}
