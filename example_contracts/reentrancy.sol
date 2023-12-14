pragma solidity ^0.4.2;

contract SimpleDAO {
  mapping (address => uint) public credit;

  function withdraw(uint amount) {
    if (credit[msg.sender]>= amount) {
      require(msg.sender.call.value(amount)());
      credit[msg.sender]-=amount;
    }
  }
}
